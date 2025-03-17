{
  description = "A Nix-flake-based Python development environment";

  inputs.nixpkgs.url = "github:nixos/nixpkgs/nixpkgs-unstable";

  outputs = { self, nixpkgs }:
    let
      supportedSystems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forEachSupportedSystem = f: nixpkgs.lib.genAttrs supportedSystems (system: f {
        pkgs = import nixpkgs { inherit system; };
      });
    in
    {
      devShells = forEachSupportedSystem ({ pkgs }: {
        default = pkgs.mkShell {
          venvDir = ".venv";
          packages = with pkgs; [ python313 ] ++
            (with pkgs.python313Packages; [
              pip
              venvShellHook
            ]);
          QT_PLUGIN_PATH="${pkgs.qt6.qtbase}/lib/qt-6/plugins";
          LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
            pkgs.libGL
            pkgs.stdenv.cc.cc.lib
            pkgs.libxkbcommon
            pkgs.fontconfig
            pkgs.xorg.libX11
            pkgs.xorg.libxcb
            pkgs.glib
            pkgs.libz
            pkgs.freetype
            pkgs.zstd
            pkgs.dbus
            pkgs.xorg.libXcursor
          ];
          # shellHook = ''
          #   bashdir=$(mktemp -d)
          #   makeWrapper "$(type -p bash)" "$bashdir/bash" "''${qtWrapperArgs[@]}"
          #   exec "$bashdir/bash"
          # '';
        };
      });
    };
}
