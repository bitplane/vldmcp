# 🕸️ vldmcp

The vision is to build a FoaF MCP library on the Veilid network, where a mixture
of bots and humans build new capabilities for bots, share code, vote on them,
share recommendations, share resources and so on.

## Overall plan

### Everything is a Service


### The CLI

* 🏗️ build identity
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

## Directory Structure

vldmcp follows the XDG Base Directory Specification for organizing its files:

### User Identity Key (Never in containers)
- **Path**: `$XDG_DATA_HOME/vldmcp/keys/user.key` (default: `~/.local/share/vldmcp/keys/user.key`)
- **Permissions**: dir `0700`, file `0600`
- **Description**: Your cryptographic identity key - never expose this to containers or services

### Node Instance Keys
- **Path**: `$XDG_STATE_HOME/vldmcp/nodes/<node-id>/` (default: `~/.local/state/vldmcp/nodes/<node-id>/`)
- **Permissions**: dir `0700`, key file `0600`
- **Description**: Per-node instance keys for server authentication

### Configuration
- **User**: `$XDG_CONFIG_HOME/vldmcp/` (default: `~/.config/vldmcp/`)
- **System**: `/etc/vldmcp/` (system-wide overrides)
- **Description**: Configuration files, systemd service files, container overrides

### Cache (Can be safely deleted)
- **Path**: `$XDG_CACHE_HOME/vldmcp/` (default: `~/.cache/vldmcp/`)
- **Contents**: Downloaded git repositories (`src/`), build artifacts (`build/`)
- **Description**: Temporary data that can be regenerated

### Application Data
- **Path**: `$XDG_DATA_HOME/vldmcp/install/` (default: `~/.local/share/vldmcp/install/`)
- **Description**: Container Dockerfiles, base images, templates

### Runtime Data
- **Path**: `$XDG_RUNTIME_DIR/vldmcp/` (default: `/tmp/vldmcp-$USER/`)
- **Permissions**: `0700`
- **Description**: PID files, Unix sockets, temporary runtime state

### Container Mount Points

When running in container mode, the following directories are mounted:

```bash
-v $XDG_STATE_HOME/vldmcp:/var/lib/vldmcp:rw      # Node state
-v $XDG_CACHE_HOME/vldmcp:/var/cache/vldmcp:rw    # Cache
-v $XDG_CONFIG_HOME/vldmcp:/etc/vldmcp:ro         # Config (read-only)
-v $XDG_RUNTIME_DIR/vldmcp:/run/vldmcp:rw         # Runtime
```

**Note**: The user identity key is never mounted into containers for security reasons.
