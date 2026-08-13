Launchpad PPA Requirements
Account Prerequisites
You Ubuntu need a Launchpad account, a GPG key to sign your source code uploads, and you must accept the Terms of Service which include the Ubuntu Code of Conduct. Signing the CoC means downloading, reading, and GPG-signing a document through your Launchpad profile.

Licensing (the big one for your app)
Content may be hosted in a PPA on Launchpad if it is approved by Canonical or released under a license which falls under one or more of the following categories. Canonical The allowed licenses are OSI-approved open source licenses (MIT, Apache 2.0, GPL, LGPL, BSD, etc.) — your standard open source licenses all qualify. This is a free service for free software developers, and licensing is limited to those specified in the PPA terms of use. Ubuntu

What You Upload
You can only upload source packages to a PPA, for security and licensing reasons — Launchpad will then build the binary packages for you. GDevNet
Launchpad will not accept uploads of packages that are unmodified from their original source in Ubuntu or Debian — only packages that include your own changes. Ubuntu This rules out just repackaging something already in the official repos without modifications.

Versioning Rules
When you upload a package, its version must exceed that of any existing package of the same name in the same Ubuntu distribution in your PPA. Ubuntu
If you're creating an alternative version of a package already available in Ubuntu's repositories, you should ensure your package supersedes the official Ubuntu version, and that future Ubuntu versions will supersede your package. To do this, add the suffix ppaN (where N is your revision number). For example: Ubuntu package myapp_1.0-1 → PPA package myapp_1.0-1ppa1. Launchpad
Version numbers must be unique. The same version cannot be reused across releases — each Ubuntu series must have a distinct package version or uploads will be rejected. Ubuntu

Changelogs
Launchpad asks that people include useful changelogs for each package so that users and other developers can understand what new features they are exploring in their work. Ubuntu This is the debian/changelog file — not optional in practice.

Storage & Build Limits
New PPAs get 8 GiB of disk space. While no strict limit is enforced on data transfer, Launchpad will get in touch if data transfer looks unusually high. Ubuntu
Launchpad will monitor total build time per user and ask people to be reasonable in their use of shared build resources. They ask that you not abuse the build system with unnecessary builds or automated uploads of large numbers of packages. Ubuntu

Supported Architectures & Formats
By default, Launchpad creates binaries for amd64. You may also request builds for arm64, armhf, i386, powerpc, ppc64el, riscv64, amd64v3, and s390x via the "Change details" page for the PPA. Ubuntu
At this stage only .deb packages are supported. Ubuntu

What This Means for Your App
Since your app is open source Python for ollama users, you almost certainly tick every box. The main things to get right are:

Pick an OSI license (MIT is simplest) and declare it in pyproject.toml and debian/control
Source-only uploads — you never upload a pre-built .deb, Launchpad builds it
Maintain a proper debian/changelog with each release
Use ppa1 version suffixes if your package name might collide with anything in the Ubuntu repos
Sign the Ubuntu Code of Conduct once during account setup — easy but easy to forget