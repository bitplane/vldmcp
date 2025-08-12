# 🕸️ vldmcp

The vision is to build a FoaF MCP library on the Veliid network, where a mixture
of bots and humans build new capabilities for bots, share code, vote on them,
share recommendations, share resources and so on.

## Overall plan

### The CLI

* 🏗️ build identit
* ⏯️ Start/stop the server + web UI
* ⏩ Delegate all calls to the HTTP API
* 🔡 and/or run the textual UI

### HTTP REST API

* 🅅 Veilid stuff
  * 📊 stats
  * 🗝️  identity management / linking accounts + keys
  * 🤖 CRUD API for peers + groups + permissions
* 🖥 Server
  * 🏗️  Container build/update
  * ⨇ Merge
* ▶ Service
  * 🔁 syncing known services and service repos with peers
  * 🔌 Add/remove start/stop services.
  * 🔍 semantic search, list with filters
  * 🩹 Return a patch that creates a new repo, pipe in into `patch`. So it
    creates a little project with instructions for them to build on.

As services are added, they are added to the API like:
    `/api/services/bitplane/0.0.1/bittty/1`

### Veilid

Services connect P2P. FoaF connections are ephemeral and done through an
introduction handshake. Veilid -> HTTP for most things.

### TUI / website

Simple TUI in Textual, served over Textual Web. Clicking stuff in the UI just
makes web service calls.

### Service manifest

Services are just git repos that we clone from (can we add a transport plugin
to git?), build in podman and spin them up. Their port gets added to the router.

Code ownership is verified via commit sigs. Veilid added to as a way to sign
code.

Manifest file in the root of the repo (JSON?) adds permissions which must be
verified. For example "r/w this path in the container" or "read this path on the
host machine", "access the GPU" etc.

Stats measured for quota.
