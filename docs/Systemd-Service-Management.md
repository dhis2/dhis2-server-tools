# service management with systemctl
The tool installs various applications such as tomcat9, postgresql, nginx, or
apache2, and sets up systemd services for managing them. Here are a few
examples:
<table>
  <tr>
    <th style="text-align: left; vertical-align: top;">Command</th>
    <th style="text-align: left; vertical-align: top;">Comments</th>
  </tr>
  <tr>
    <td style="vertical-align: top; text-align: left;"><code>systemctl stop  postgresql</code></td>
    <td>Stops a postgresql Service</td>
  </tr>
  <tr>
    <td style="vertical-align: top; text-align: left;"><code>systemctl start   postgresql</code></td>
    <td>Start postgresql Service</td>
  </tr>
  <tr>
    <td style="vertical-align: top; text-align: left;"><code> systemctl restart postgresql </code></td>
    <td>Restarts PostgreSQL service</td>
  </tr>
  <tr>
    <td style="vertical-align: top; text-align: left;"><code>systemctl  stop tomcat9 </code></td>
    <td>Stops Tomcat9 Service </td>
  </tr>
  <tr>
    <td style="vertical-align: top; text-align: left;"><code>systemctl  start tomcat9 </code></td>
    <td>Starts Tomcat9 Service <br></td>
  </tr>
  <tr>
    <td style="vertical-align: top; text-align: left;"><code>systemctl  restart tomcat9</code></td>
    <td>Restarts Tomcat9 Service </td>
  </tr>
</table>
