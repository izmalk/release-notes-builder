# **Spec** DA186 - Release notes for Data charms 

## **Abstract**

This specification establishes a minimal, consistent framework to ensure that every stable release is properly documented and easily accessible.

The scope of this spec is limited to the structure and contents of release notes. For implementation details, there will be another spec later.

## **Rationale**

Release notes are a critical communication tool between engineering teams and their users. They provide a clear, structured record of what has changed, what new features or fixes are included, and any important compatibility considerations. 

By setting a standard for how release notes are presented, we help users navigate product updates more confidently and maintain a higher level of trust in the quality and stability of our releases. Release notes support transparency, operational continuity, and better decision-making for all stakeholders.

## **Specification**

Each stable release of a charmed Data\&AI product **can** include the following documents:

* (mandatory) **Release notes** – A full list of changes in a stable release, with some highlights and useful references. Usually published in GitHub Releases notes and Reference section of documentation. Optimised for transparency and visibility.   
* (optional) **Press release** – Engaging text optimised for human readability and marketing. Usually published on the Discourse forum and/or social networks. Optimised to drive engagement among users.  
* (optional) **Change log** – An accumulative list of changes for each stable release (includes all previous stable releases too). Usually stored as a file in the repository with the source code. Optimised for searching and skimming through.

### **Release notes**

Each product release to a stable risk channel **must** have an associated release notes page, referred to hereafter as *release page*. A release page should be located in the *Release notes* or *Releases* section within the *Reference* part of the product's documentation.

A title of a release page must contain charm’s revision or some other type of unique release version designation. The exact date of the release should be added after the title.

A release page must have three main sections:

* Introduction  
* List of changes  
* Compatibility information

#### **Introduction**

An Introduction section is the very first part of release notes and must introduce the release to potential users in a readable form. It consists of a brief summary of the most important changes, as well as links to:

* The most relevant charm’s page on Charmhub  
* How to upgrade guide and any specific upgrade instructions  
* How to deploy guide  
* System requirements page

#### **List of changes**

The list of changes section is the most important part of release notes.  
It contains a full list of changes since the previous stable release, distributed among categories.

The list of possible categories for changes in release notes:

* **Features** – new functionality, expanding capabilities.  
* **Breaking changes** – changes that break backwards compatibility (e.g., deprecating a feature).  
* **Security** – vulnerability fixes (e.g. CVE fixes, etc.).  
* **Bug fixes** – fix errors, typos, undesired behaviour, etc.  
* **Other improvements** – everything else, including documentation, refactoring, build and CI improvements, performance and test enhancement.

An empty category must be omitted from release notes completely.

Each element in the list should include a link to a respective PR, commit message, or both.

#### **Compatibility information**

This section contains information about workload versions, as well as software and hardware compatibility of this particular release of a product.

Workload versions can be represented by any combination of workload software, rocks, and snaps versions.

Software compatibility information must list required software dependencies, supported Juju versions, as well as other software components if needed. It may also note constraints on other charms or software, that can be used but aren’t required.

Hardware compatibility information must include a list of supported hardware architectures. If there are separate revisions of a charm for different architectures, it must provide a clear way to identify the revision needed for any particular architecture. This section can include known constraints on compatible hardware.

##### **Known issues**

Optionally, a Known issues section can be added at the end with a list of known bugs and vulnerabilities, including the ones from upstream/ workload.   
This section can be added later (to existing release notes) if a new vulnerability is found.  
This section can be edited later in existing release notes to add a link to a fix and mark the issue as resolved.
