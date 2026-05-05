# PackServer

A simple Minecraft Resource Pack server

## NixOS module

This flake exports a NixOS module at `nixosModules.default` with options under `services.packserver.*`.

Example:

```nix
{
  inputs.packserver.url = "github:jone-cmd/packserver";

  outputs = { self, nixpkgs, packserver, ... }: {
    nixosConfigurations.my-host = nixpkgs.lib.nixosSystem {
      system = "x86_64-linux";
      modules = [
        packserver.nixosModules.default
        {
          services.packserver = {
            enable = true;
            serverManagementEndpoint = "wss://server.example.invalid";
            token = "replace-me";
            packFile = "/var/lib/packserver/resourcepack.zip";
            host = "0.0.0.0";
            port = 8000;
            openFirewall = true;
          };
        }
      ];
    };
  };
}
```
