with import <nixpkgs> {};
(python38.withPackages (ps: [ps.youtube-dl])).env

