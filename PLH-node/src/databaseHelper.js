import { CosmosClient } from "@azure/cosmos";

const COSMOS_DB_ENDPOINT = process.env.COSMOS_DB_ENDPOINT;
const COSMOS_DB_KEY = process.env.COSMOS_DB_KEY;

const azure_client = new CosmosClient({ endpoint: COSMOS_DB_ENDPOINT, key: COSMOS_DB_KEY });

const { database } = await azure_client.databases.createIfNotExists({ id: "Messages" });
const { container } = await database.containers.createIfNotExists({ id: "Items" });

export const getChatHistory = async (chat_id) => {
  const { resources: chatHistory } = await container.items
    .query({
      query: "SELECT * FROM c WHERE c.chat_id = @chat_id",
      parameters: [{ name: "@chat_id", value: chat_id }],
    })
    .fetchAll();
  return chatHistory;
};

export const upsertMessage = async (message) => {
  await container.items.upsert(message);
};
