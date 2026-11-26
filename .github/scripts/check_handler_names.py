#!/usr/bin/env python3
"""Fail if role handler names could resolve to another role's handler.

All roles in a play share one handler namespace, and when two roles define a
handler with the same name only the last-defined one runs. If that copy is
skipped (e.g. its role has a `when:`), the notifying role's change is never
applied (see the "Restart Grafana" / alerting bug). This check enforces:

  1. every handler name under roles/*/handlers/ is unique across roles;
  2. every `notify:` in a role's tasks/handlers names a handler that the same
     role defines (Jinja in the notify, e.g. "Reload {{ proxy | capitalize }}
     (proxy)", is matched as a wildcard).

Usage: python3 .github/scripts/check_handler_names.py deploy
"""
import collections
import glob
import os
import re
import sys

import yaml


def load(path):
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def notifies(node, out):
    if isinstance(node, dict):
        if "notify" in node:
            value = node["notify"]
            out.extend(value if isinstance(value, list) else [value])
        for child in node.values():
            notifies(child, out)
    elif isinstance(node, list):
        for child in node:
            notifies(child, out)


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else "deploy"
    roles_dir = os.path.join(base, "roles")
    defined = collections.defaultdict(set)   # role -> handler names
    owners = collections.defaultdict(list)   # handler name -> roles
    errors = []

    for role in sorted(os.listdir(roles_dir)):
        for path in sorted(glob.glob(os.path.join(roles_dir, role, "handlers", "*.yml"))):
            for handler in load(path) or []:
                name = handler.get("name")
                if name:
                    defined[role].add(name)
                    owners[name].append(role)

    for name, roles in sorted(owners.items()):
        if len(set(roles)) > 1:
            errors.append(f"handler '{name}' is defined in several roles: {', '.join(sorted(set(roles)))}")

    for role in sorted(os.listdir(roles_dir)):
        files = glob.glob(os.path.join(roles_dir, role, "tasks", "**", "*.yml"), recursive=True)
        files += glob.glob(os.path.join(roles_dir, role, "handlers", "*.yml"))
        for path in sorted(files):
            found = []
            notifies(load(path), found)
            for name in found:
                if not isinstance(name, str):
                    continue
                pattern = "^" + re.sub(r"\\\{\\\{.*?\\\}\\\}", ".+", re.escape(name)) + "$"
                if not any(re.match(pattern, h) for h in defined[role]):
                    rel = os.path.relpath(path, base)
                    errors.append(f"{rel}: notifies '{name}', which role '{role}' does not define")

    for err in errors:
        print(f"ERROR: {err}")
    if errors:
        print(f"\n{len(errors)} handler naming problem(s). Suffix handler names with the role, "
              "e.g. 'Reload Nginx (proxy)', and define every notified handler in the same role.")
        return 1
    print("Handler names OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
