# 🕸️ vldmcp

The vision is to build a FoaF MCP library on the Veilid network, where a mixture
of bots and humans build new capabilities for bots, share code, vote on them,
share recommendations, share resources and so on.

## Overall plan

Note: I'm talking like this is a done deal here, but it's far from complete.

### Everything is a Service

It's all a bunch of nested services that can be accessed like a filesystem.
MCP services don't get IO by default, they have to call the (their or a)
StorageService, same with networking. Remote-built services are stdio/stdio
only by default, but this can't be enforced unless you're using containers.

Calling a method on a service is down to having an identity with the right
permissions. All of vldmcp's internals are also services, so anyone or thing
can introspect it and call methods if the owner says so.

The docstrings of your services are the source of truth, and will be indexed
so they can be searched for by man or womachine.

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

### MVPs and NCPs

Users are identified by a key. Services are signed by the user's key. Every
service also has its own key, though it might share its parent's if its parent
feels extra generous.

When a vldmcp server comes online, it publishes a list of boxes owned/signed by
the same user, and announces itself to its peers. They can then query it and
get a list of services, assuming they trust it. Services can be called, or
downloaded and run locally. Sevices have metadata like capacity, and I might
even add queues.

Identities have a provider, and users can map identities together. This can
be done by git signing key, or by some random URL. Whatever you write I guess.

### Method Dispatch

The initiating call is signed by a key that belongs to you, and each call adds
more weight to the signature chain. This is required for blacklisting /
whitelisting.

Each service is a collection of methods, and may have its own/sub/services.
Methods are wrapped with a decorator that captures the function signature,
wrapping the call and return values into Pydantic object model with added
metadata, and compiled to capnproto.

When called, a context is passed as part of the metadata. This allows
fine-grained permissions, like allowing only methods called from this class to
have access to the local storage service, to make outbound network connections
to certain domains, or to otherwise filter and limit the allowed calls.

In the return value, performance statistics are gathered and are automatically
sampled by the runtime. This allows quota management.


### Permissions

Services themselves have requirements, disk, RAM, GPU, and access to other
services. You'll get an itinery of what's needed before installing it. You can
override these, group them into roles, assign roles to users etc.

### Truthiness

Users can publish claims and search for them. This might be about the outcome
of some service (like an oracle), the performance of a service, the
trustworthiness of a user or data source. The context including service method
chains git hashes and signatures, can be saved with the data, and the hash of
this claim shared.

explicit/implicit/automatic/unknown: set by user, peer, bot, or not set

sample count, confidence

## `CURRENT_STATE`

I have some nice server classes and a podman in podman setup, key generation, a
web server, Dockerfile, nginx config and need light refactoring before moving on
to the next stages.

### todo

#### The CLI

~~* 🏗️ build identity~~
~~* ⏯️ Start/stop the server + web UI~~
~~* ⏩ Delegate all calls to the HTTP API~~
* 🔡 and/or run the textual UI

#### HTTP REST API

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
* Proxies
  * veilid -> http
  * http   -> veilid
  * python -> http

### TUI

* 🗔  Basic front-end
  * 🕸 textual-web
* 📖 API/MCP browser
  * 🔩 custom widgets


## Directory Structure

- `$XDG_STATE_HOME/vldmcp/nodes/<node-id>/` (default: `~/.local/state/vldmcp/nodes/<node-id>/`)
-`$XDG_CONFIG_HOME/vldmcp/` (default: `~/.config/vldmcp/`)
-`$XDG_CACHE_HOME/vldmcp/` (default: `~/.cache/vldmcp/`)
-`$XDG_DATA_HOME/vldmcp/install/` (default: `~/.local/share/vldmcp/install/`)
-`$XDG_RUNTIME_DIR/vldmcp/` (default: `/tmp/vldmcp-$USER/`)
