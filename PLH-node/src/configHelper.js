import fs from "fs";
import yaml from "yaml";

class ConfigHelper {
  constructor(lng) {
    try {
      const filePath = lng === "es" ? "config-es.yaml" : "config.yaml";
      const file = fs.readFileSync(filePath, "utf8");
      this.config = yaml.parse(file);
    } catch (error) {
      console.error("error", error);
      throw new Error("Failed to read config file", error);
    }
  }

  getConfig() {
    return this.config;
  }
}

export default ConfigHelper;
