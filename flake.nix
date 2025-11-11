{
  description = "Nix Flake for Streaming XML Reader with lxml";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  };

  outputs = { self, nixpkgs }: let
    system = "x86_64-linux";
    pkgs = import nixpkgs { inherit system; };
  in {
    # Development shell
    devShells.${system}.default = with pkgs; mkShell {
      buildInputs = [
        python313
        python313Packages.lxml
        python313Packages.aiofiles
        libxml2
        libxslt

        nixfmt-rfc-style
        nixd
        uv
        memray
      ];

      shellHook = ''
        echo "Nix Flake dev shell ready with Python + lxml"
      '';
    };

    # Docker image
    packages.${system}.dockerImage = with pkgs; dockerTools.buildImage {
      name = "xmlreader";
      tag = "latest";
      contents = [
        python313Full
        python313Packages.lxml
        libxml2
        libxslt
        # optional: any other dependencies
      ];
      config = {
        Cmd = [ "python" "/app/streaming_xml_reader.py" ];
      };
    };
  };
}
