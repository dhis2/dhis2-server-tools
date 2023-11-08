# DHIS2 version upgrade guide
Table of contents
<!-- vim-markdown-toc GFM -->

* [Introduction](#introduction)
* [Upgrading DHIS2 (Short version)](#upgrading-dhis2-short-version)
* [Detailed considerations](#detailed-considerations)
	* [Backup and restore tips and tricks](#backup-and-restore-tips-and-tricks)
	* [Assessing Server Requirements for upgrade](#assessing-server-requirements-for-upgrade)
	* [Software requirements for the new version](#software-requirements-for-the-new-version)
	* [What if you also need to upgrade other components like the OS and database etc.](#what-if-you-also-need-to-upgrade-other-components-like-the-os-and-database-etc)
	* [How do you assess the existing metadata](#how-do-you-assess-the-existing-metadata)
	* [How do you test](#how-do-you-test)
* [The Upgrade calendar (example)](#the-upgrade-calendar-example)

<!-- vim-markdown-toc -->


## Introduction

This document outlines the procedure for upgrading the DHIS2 application on an
Ubuntu server. It serves as a comprehensive guide, highlighting best practices
to adhere to during the upgrade.

Numerous factors motivate the upgrade of the DHIS2 application and its
associated components. Newer versions often bring bug fixes, enhanced security
measures, and additional features.

There are two categories of upgrades: Minor version upgrades and Major version
upgrades. Typically, minor version upgrades don't introduce breaking changes.

While upgrading may seem straightforward—primarily entailing the replacement of
the dhis2.war file with its latest version—various complications can arise.
Issues can stem from resource limitations, unexpected changes in the new
version, an incomplete upgrade process, among others. Therefore, it's essential
to strategize and plan the upgrade process meticulously.



* Who is this document for
* Why do we need to upgrade
* Types of upgrade
* Backing up and moving 
    * static files
    * dhis.conf
    * database
    * war file
* Making an upgrade plan
    * prepare an upgrade schedule. 
    * testing phase
    * training phase
    * Switchover phase
        * Eg. Monday morning or a Friday evening? Compensation for working on the weekend
* Who needs to be involved
    * Don't forget the users
    * And the person responsible for the DNS
* Post Upgrade 
    * backup configuration
    * monitoring 
    * optimizations, 


## Upgrading DHIS2 (Short version)

<table>
  <tr>
   <td style="vertical-align: top; text-align: left;">Step </td>
   <td style="vertical-align: top; text-align: left;">Task </td>
   <td style="vertical-align: top; text-align: left;">Description </td>
   <td style="vertical-align: top; text-align: left;">Status </td>
  </tr>
  <tr>
  <td style="vertical-align: top; text-align: left;">1 </td>
   <td style="vertical-align: top; text-align: left;">Planning </td>
   <td style="vertical-align: top; text-align: left;">
   Identification of all National systems and critical custom applications, Versions for the different instances 
<ul>
<li>Custom Applications
<li>Software versions (java,tomcat, dhis2,PostgreSQL, nginx/apache2 proxy etc )
<li>Resources - Test server availability. 
<li>Scope - Does it include OS and the database ?.
</li> </ul> </td>
<td style="vertical-align: top; text-align: left;">
<ul>
<li>Pending
<li>ongoing
<li>completed 
</li> </ul> </td> </tr>
<tr>
   <td style="vertical-align: top; text-align: left;">2 </td>
   <td style="vertical-align: top; text-align: left;">Backup Current System </td>
   <td style="vertical-align: top; text-align: left;">Identify backup Environment and required specification. Do backups for at least below items:-  
      <ul>
	 <li>DHIS2 database, 
	 <li>configuration files, 
	 <li>custom apps, 
	 <li>any external integration.
      </ul>
      Backup documentation 
      <ul> <li>Take note of the time for backups dumps </li> </ul>
   </td>

   <td style="vertical-align: top; text-align: left;">
      <ul>
	    <li>Pending
	    <li>ongoing
	    <li>completed 
	    </li>
      </ul>
   </td>
</tr>

<tr>
   <td style="vertical-align: top; text-align: left;">3 </td>
   <td style="vertical-align: top; text-align: left;">Review DHIS2 Release Notes </td>
   <td style="vertical-align: top; text-align: left;">Go through the release notes of the new version to understand 
<ul>

<li>new features, 

<li>fixes

<li>potential breaking changes.
</li>
</ul>
   </td>
   <td style="vertical-align: top; text-align: left;"> </td>
  </tr>
  <tr>
   <td style="vertical-align: top; text-align: left;">4 </td>
   <td style="vertical-align: top; text-align: left;">Set Up Staging Environment </td>
   <td style="vertical-align: top; text-align: left;">Replicate the production setup in a staging environment. Create test cases and test environment on the staging. 
<p>
This will be used to test the upgrade before it's applied to production.
<ul>
<li>Keep versions as is on prod, 
<li>restore prod database, take note of the time for restore
<li>Ensure staging works as prod 
</li>
</ul> </td>
   <td style="vertical-align: top; text-align: left;"> </td>
  </tr>
  <tr>
   <td style="vertical-align: top; text-align: left;">5 </td>
   <td style="vertical-align: top; text-align: left;">Test Upgrade on Staging </td>
   <td style="vertical-align: top; text-align: left;">Implement the upgrade on the staging environment to identify any issues or conflicts.
<p>
Involve users during testing process
   <ul>
      <li> Perform Metadata Cleanup using the tool <a href="https://github.com/dhis2/metadata-assessment">here</a>
      <li>implement test cases created
      <li>Test and validate applications and functionalities
      <li>Fixing of issues identified
      </li>
   </ul>
   </td>
   <td style="vertical-align: top; text-align: left;">
   </td>
  </tr>
     <tr>
	 <td style="vertical-align: top; text-align: left;">6 </td>
	 <td style="vertical-align: top; text-align: left;">Notify Stakeholders </td>
	 <td style="vertical-align: top; text-align: left;">Inform all DHIS2 users about the planned upgrade and expected downtime. This ensures all users are prepared for the outage. </td>
	 <td style="vertical-align: top; text-align: left;"> </td>
     </tr>
      <tr>
	 <td style="vertical-align: top; text-align: left;">7 </td>
	 <td style="vertical-align: top; text-align: left;">Create  roll-back Plan </td>
	 <td style="vertical-align: top; text-align: left;">Backup up the DHIS2 instance (both application and database) as a rollback strategy in case of any total data loss or considerable loss in functionality </td>
	 <td style="vertical-align: top; text-align: left;"> </td>
     </tr>
     <tr>
	 <td style="vertical-align: top; text-align: left;">8 </td>
	 <td style="vertical-align: top; text-align: left;">Upgrade Production </td>
	 <td style="vertical-align: top; text-align: left;">Once satisfied with the staging tests, apply the upgrade to the production system. </td>
	 <td style="vertical-align: top; text-align: left;"> </td>
     </tr>
     <tr>
	 <td style="vertical-align: top; text-align: left;">9 </td>
	 <td style="vertical-align: top; text-align: left;">Post-Upgrade Testing </td>
	 <td style="vertical-align: top; text-align: left;">Test the main functions in the production environment to ensure everything is working correctly after the upgrade. </td>
	 <td style="vertical-align: top; text-align: left;"> </td>
     </tr>
     <tr>
	 <td style="vertical-align: top; text-align: left;">19 </td>
	 <td style="vertical-align: top; text-align: left;">Monitor System </td>
	 <td style="vertical-align: top; text-align: left;">Continuously monitor system performance and logs to catch any unexpected issues early. </td>
	 <td style="vertical-align: top; text-align: left;"> </td>
     </tr>
     <tr>
	 <td style="vertical-align: top; text-align: left;">11 </td>
	 <td style="vertical-align: top; text-align: left;">Document Process </td>
	 <td style="vertical-align: top; text-align: left;">Document the upgrade process, any challenges faced, solutions used, and lessons learned for future reference. </td>
	 <td style="vertical-align: top; text-align: left;"> </td>
     </tr>
     <tr>
	 <td style="vertical-align: top; text-align: left;">12 </td>
	 <td style="vertical-align: top; text-align: left;">Gather User Feedback </td>
	 <td style="vertical-align: top; text-align: left;">Collect feedback from DHIS2 users on the new version's performance, features, and any potential issues they're facing post-upgrade. </td>
	 <td style="vertical-align: top; text-align: left;"> </td>
     </tr>
</table>

## Detailed considerations

### Backup and restore tips and tricks

* Backup Tips:
   * Ensure you have enough disk storage for storing local backups. use` df -h
     `command to check available disk space on your server.
   * Ensure you have remote location for storing your backups.
      
      It can be and object storage end point, Network Attached Storage (NAS),
      some backup server with sufficient storage, 
   * Versioning - Consider using versioned backups, which allow you to restore
     to a specific point in time, not just the latest backup.
   * Encryption: Encrypt your backups to secure your data, especially if it
     contains sensitive information
   * Documentation: Document your restore procedures and keep them in an easily
     accessible location. This can save valuable time during a crisis.
   * Cloud Backups: Utilize cloud-based backup solutions for scalability,
     redundancy, and ease of access.
   * Snapshot Backups: If your infrastructure supports it, use snapshot backups
     to create point-in-time copies of your data and systems.
   * Compression: Compress your backups to reduce storage requirements and
     speed up backup and restore processes.

*  Restoring Tips:
   * Test Restores: - Regularly be testing your backup restoration, take note
     of how long it takes, and ensure it works as expected. A backup is only
     valuable if you can restore from it. 
   * Validation: Even after restore, validate that your data is intact, and
     applications are functioning as expected. 

### Assessing Server Requirements for upgrade

* _RAM:_ At least 4 GB for a small instance, 12 GB for a medium instance, 64 GB
  or more for a large instance.
* _CPU cores:_ 4 CPU cores for a small instance, 8 CPU cores or more for a
  medium or large instance.
* _Disk:_ SSD is recommended as a storage device. The minimum read speed is 150
  Mb/s, 200 Mb/s is good, and 350 Mb/s or better is ideal. In terms of disk
  space, at least 100 GB is recommended, but it will depend entirely on the
  amount of data which is contained in the data value tables. Analytics tables
  require a significant amount of disk space. Plan and ensure your server can
  be upgraded with more disk space.

### Software requirements for the new version
Later DHIS2 versions require the following software versions to operate.

1. An operating system for which a Java JDK or JRE version 8 or 11 exists.
   Linux is recommended.
2. Java JDK. OpenJDK is recommended.
    1. For DHIS2 version 2.38 and later, JDK 11 is required.
    2. For DHIS2 version 2.35 and later, JDK 11 is recommended and JDK 8 or
       later is required.
    3. For DHIS2 versions older than 2.35, JDK 8 is required.
    4. For DHIS2 Versions 2.41 and later, JDK 17 is required. 
3. PostgreSQL database version 9.6 or later. A later PostgreSQL version such as
   version 13 is recommended.
4. PostGIS database extension version 2.2 or later.
5. Tomcat servlet container version 8.5.50 or later, or other Servlet API 3.1
   compliant servlet containers.

### What if you also need to upgrade other components like the OS and database etc.

If you need to upgrade base OS, and other components, the recommended approach
is to setup a new environment, with the required OS version and databases for
example, 

### How do you assess the existing metadata

One of the most common causes of upgrade failure is that anomalies in the
existing metadata might be “acceptable” on the existing version but cause
errors on the new version.  Taking the opportunity of the upgrade to do a
cleanup of your metadata is a useful thing to do and also helps you avoid
problems with the upgrade.


* Run the metadata assessment scripts on the test instance (before upgrading)

    [https://github.com/dhis2/metadata-assessment](https://github.com/dhis2/metadata-assessment)

* Fix as much as you can fix

### How do you test
* Make a checklist
* Involve users
* Identifying errors in log files
* Performance measures

## The Upgrade calendar (example)
<table>
     <tr>
	 <td style="vertical-align: top; text-align: left;"><strong>Month</strong> </td>
	 <td style="vertical-align: top; text-align: left;"><strong>Activity</strong> </td>
	 <td style="vertical-align: top; text-align: left;"><strong>Resource implication</strong> </td>
     </tr>
  <tr>
      <td style="vertical-align: top; text-align: left;">April (pre-release) </td>
      <td style="vertical-align: top; text-align: left;">Metadata assessment
      and cleanup <p> Start testing, potentially join beta testing program
      </td>
      <td style="vertical-align: top; text-align: left;">Human resource for
      metadata cleanup <p> Server resource for testing <p> Sysadmin resource
      for installation <p> Human resources for testing. </td>
  </tr>
  <tr>
   <td style="vertical-align: top; text-align: left;">May (new release)
   </td>
   <td style="vertical-align: top; text-align: left;">Test release.  
<p>
Start planning for training, training of trainers, online materials etc
   </td>
   <td style="vertical-align: top; text-align: left;">Server resource for testing
<p>
Human resource for training preparation and training of TOT
   </td>
  </tr>
  <tr>
   <td style="vertical-align: top; text-align: left;">June
   </td>
   <td style="vertical-align: top; text-align: left;">Training
   </td>
   <td style="vertical-align: top; text-align: left;">Sysadmin resource for installation
<p>
Server resource for training
<p>
Provision of physical or virtual training events </td>
  </tr>
     <tr>
	 <td style="vertical-align: top; text-align: left;">July </td>
	 <td style="vertical-align: top; text-align: left;">Upgrade production </td>
	 <td style="vertical-align: top; text-align: left;">Sysadmin resource for installation </td>
     </tr>
</table>

