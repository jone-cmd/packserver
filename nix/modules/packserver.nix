self:
{
  config,
  lib,
  pkgs,
  ...
}:
let
  cfg = config.services.packserver;
  inherit (lib)
    mkEnableOption
    mkIf
    mkOption
    types
    ;
in
{
  options.services.packserver = {
    enable = mkEnableOption "PackServer";

    package = mkOption {
      type = types.package;
      default = self.packages.${pkgs.system}.default;
      defaultText = "self.packages.${pkgs.system}.default";
      description = "PackServer package to run.";
    };

    serverManagementEndpoint = mkOption {
      type = types.str;
      example = "wss://server.example.invalid/ws";
      description = "Minecraft server management websocket endpoint.";
    };

    token = mkOption {
      type = types.str;
      description = "Bearer token for the server management endpoint.";
    };

    host = mkOption {
      type = types.str;
      default = "0.0.0.0";
      description = "Host/address to bind PackServer to.";
    };

    port = mkOption {
      type = types.port;
      default = 8000;
      description = "Port to bind PackServer to.";
    };

    packFile = mkOption {
      type = types.str;
      example = "/var/lib/packserver/resourcepack.zip";
      description = "Path to the resource pack ZIP file.";
    };

    openFirewall = mkOption {
      type = types.bool;
      default = false;
      description = "Whether to open the selected port in the firewall.";
    };

    user = mkOption {
      type = types.str;
      default = "packserver";
      description = "User account under which PackServer runs.";
    };

    group = mkOption {
      type = types.str;
      default = "packserver";
      description = "Group account under which PackServer runs.";
    };

    dir = mkOption {
      type = types.str;
      default = "/var/lib/packserver";
      description = "Working directory for PackServer.";
    };

    createUser = mkOption {
      type = types.bool;
      default = true;
      description = "Whether to create the configured user and group automatically.";
    };

    debug = mkOption {
      type = types.bool;
      default = false;
      description = "Whether to enable debug logging for PackServer.";
    };
  };

  config = mkIf cfg.enable {
    networking.firewall.allowedTCPPorts = mkIf cfg.openFirewall [ cfg.port ];

    users.groups = mkIf cfg.createUser { ${cfg.group} = { }; };
    users.users = mkIf cfg.createUser {
      ${cfg.user} = {
        isSystemUser = true;
        group = cfg.group;
        home = cfg.dir;
        createHome = true;
      };
    };

    systemd.services.packserver = {
      description = "PackServer";
      wantedBy = [ "multi-user.target" ];
      after = [ "network-online.target" ];
      wants = [ "network-online.target" ];
      serviceConfig = {
        Type = "simple";
        DynamicUser = false;
        User = cfg.user;
        Group = cfg.group;
        WorkingDirectory = cfg.dir;
        Restart = "on-failure";
        RestartSec = "5s";
      };
      script = ''
        exec ${cfg.package}/bin/packserver \
          ${lib.escapeShellArg cfg.serverManagementEndpoint} \
          ${lib.escapeShellArg cfg.token} \
          --host ${lib.escapeShellArg cfg.host} \
          --port ${toString cfg.port} \
          --pack-file ${lib.escapeShellArg cfg.packFile}
          ${if cfg.debug then "--debug" else ""}
      '';
    };
  };
}
