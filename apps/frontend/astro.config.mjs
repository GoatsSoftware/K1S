import node from "@astrojs/node";
import { defineConfig } from "astro/config";

export default defineConfig({
  output: "server",
  adapter: node({ mode: "standalone" }),
  // Requests come through the gateway proxy / port forwarding, so Origin can differ.
  security: { checkOrigin: false },
});
