#include "multiplayer.h"
#include <enet/enet.h>
#include <startup/dag_globalSettings.h>
#include <debug/dag_debug.h>
#include <cstdlib>
#include <cstring>

namespace multiplayer
{
static ENetHost *host = nullptr;
static bool server = false;
static bool ready = false;
static int readyPeers = 0;
static const char hello[] = "DAGOR_TEMPLATE_V1";
static const char welcome[] = "DAGOR_WELCOME_V1";

bool initialize()
{
  const char *remote = dgs_get_argv("connect");
  const char *portString = dgs_get_argv("port", "27015");
  char *end = nullptr;
  const unsigned long port = strtoul(portString, &end, 10);
  if (!end || *end || port == 0 || port > 65535 || enet_initialize() != 0)
    return false;
  server = remote == nullptr;
  ENetAddress address{};
  address.host = ENET_HOST_ANY;
  address.port = static_cast<enet_uint16>(port);
  host = enet_host_create(server ? &address : nullptr, 16, 1, 0, 0);
  if (!host)
  {
    enet_deinitialize();
    return false;
  }
  host->maximumPacketSize = 1024;
  host->maximumWaitingData = 64 * 1024;
  if (!server && (enet_address_set_host(&address, remote) != 0 || !enet_host_connect(host, &address, 1, 0)))
  {
    shutdown();
    return false;
  }
  debug("multiplayer: %s on port %lu", server ? "hosting" : "connecting", port);
  return true;
}

void update()
{
  ENetEvent event{};
  // Bound networking work per game update instead of blocking the render loop.
  for (int count = 0; count < 64 && enet_host_service(host, &event, 0) > 0; ++count)
    switch (event.type)
    {
      case ENET_EVENT_TYPE_CONNECT:
        if (!server)
          enet_peer_send(event.peer, 0, enet_packet_create(hello, sizeof(hello), ENET_PACKET_FLAG_RELIABLE));
        break;
      case ENET_EVENT_TYPE_RECEIVE:
        if (server && event.packet->dataLength == sizeof(hello) && memcmp(event.packet->data, hello, sizeof(hello)) == 0)
        {
          enet_peer_send(event.peer, 0, enet_packet_create(welcome, sizeof(welcome), ENET_PACKET_FLAG_RELIABLE));
          if (event.peer->data != host)
          {
            event.peer->data = host;
            ++readyPeers;
          }
          ready = readyPeers > 0;
          debug("multiplayer: handshake complete (host)");
        }
        else if (!server && event.packet->dataLength == sizeof(welcome) && memcmp(event.packet->data, welcome, sizeof(welcome)) == 0)
        {
          ready = true;
          debug("multiplayer: handshake complete (client)");
        }
        enet_packet_destroy(event.packet);
        break;
      case ENET_EVENT_TYPE_DISCONNECT:
        if (server && event.peer->data == host)
        {
          event.peer->data = nullptr;
          --readyPeers;
        }
        ready = server && readyPeers > 0;
        debug("multiplayer: peer disconnected");
        break;
      default: break;
    }
  enet_host_flush(host);
}

void shutdown()
{
  if (host)
  {
    enet_host_destroy(host);
    host = nullptr;
    enet_deinitialize();
  }
  ready = false;
  readyPeers = 0;
}
bool connected() { return ready; }
}
