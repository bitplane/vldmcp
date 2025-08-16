# 🕸️ vldmcp

The vision is to build a FoaF MCP library on the Veilid network, where a mixture
of bots and humans build new capabilities for bots, share code, vote on them,
share recommendations, share resources and so on.

## Overall plan

### Everything is a Service

It's all a bunch of nested services that can be accessed like a filesystem.
MCP services don't get IO by default, they have to call the (their or a)
StorageService, same with networking. MCP services are stdio/stdio

Calling a method on a service is done by having an identity with the right
permissions. All of vldmcp's internals are also services, so anyone or thing
can introspect it and call methods if they have permissions.

Method dispatch works by embedding the signature of the call and its return
type in a Pydantic object model, and proxied via location in the API directory.

Each/path/segment in this example is a different node in a tree of services:

        /api/github.com:bitplane/host1/mcp/mvp-mcp:1.0.0+abcdef1/knickers-off
          |     |        |         |    |      |     |      |       |
          v     |        |         |    |      |     |      |       v
    api root    v        |         |    |      |     |      v    what it does
           id provider   v         |    |      |     |  commit hash
                my username        v    |      v  version no
                    memorable box name  v  the service
                                mcp services

Because it's using FastAPI and Pydantic, you can get a swagger interface at
the /doc/ endpoint, but I wouldn't recommend it. That's why the Textual and
Textual web interfaces (will) exist.

When sharing links, you'll need to connect to GitHub/GitLab/Radicle if you want
a short URL like that one.


### Identity

Users are identified by a key. Services are signed by the user's key. When a
vldmcp server comes online


### Permissions



### The CLI

~~* 🏗️ build identity~~
~~* ⏯️ Start/stop the server + web UI~~
~~* ⏩ Delegate all calls to the HTTP API~~
* 🔡 and/or run the textual UI

### HTTP REST API

* 🅅 Veilid stuff
  * 📊 stats
  * 🗝️  identity management / linking accounts + keys
  * 🤖 CRUD API for peers + groups + permissions
* 🖥 Server
  ~~* 🏗️  Container build/updae~~
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
introduction handshake.

### TUI / website

Simple TUI in Textual, served over Textual Web. Clicking stuff in the UI just
makes web service calls.

### MCP Services

MCP services are generated from git repos that we clone from, build in Docker
or Podman, get them to dump an API spec and then spin them up.

Code ownership is verified via commit sigs, with Veilid added to as a way to
sign code.

Manifest file in the root of the repo (toml) adds permissions which must be
verified before installing. For example "r/w this path in the container" or
"read this path on the host machine", "access the GPU", "call this specific
service pattern" and so on.

##


## Directory Structure

XDG dirs apply:

### User Identity Key
- **Path**: `$XDG_DATA_HOME/vldmcp/keys/user.key` (`~/.local/share/vldmcp/keys/user.key`)
- **Description**: Your cryptographic identity key - never expose this to containers or services

### Node Instance Keys
- **Path**: `$XDG_STATE_HOME/vldmcp/nodes/<node-id>/` (default: `~/.local/state/vldmcp/nodes/<node-id>/`)
- **Description**: Per-node instance keys for server authentication

### Configuration
- **User**: `$XDG_CONFIG_HOME/vldmcp/` (default: `~/.config/vldmcp/`)
- **System**: `/etc/vldmcp/` (system-wide overrides)
- **Description**: Configuration files, systemd service files, container overrides

### Cache (Can be safely deleted)
- **Path**: `$XDG_CACHE_HOME/vldmcp/` (default: `~/.cache/vldmcp/`)
- **Contents**: Downloaded git repositories (`src/`), build artifacts (`build/`)
- **Description**: Temporary data that can be downloaded again.

### Application Data
- **Path**: `$XDG_DATA_HOME/vldmcp/install/` (default: `~/.local/share/vldmcp/install/`)
- **Description**: Container Dockerfiles, base images, templates; stuff we need
  to be able to run the thing.

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
