import { Client, GatewayIntentBits, Interaction } from 'discord.js';
import { env } from './config/env';
import { runMigrations } from './db/database';
import { CatalogService } from './services/catalogService';
import { CommandHandler } from './commands/handler';

runMigrations();

const catalog = new CatalogService();
catalog.load();

const handler = new CommandHandler(catalog);

const client = new Client({ intents: [GatewayIntentBits.Guilds] });

client.once('ready', () => {
  console.log(`Bot logged in as ${client.user?.tag}`);
});

client.on('interactionCreate', async (interaction: Interaction) => {
  if (!interaction.isChatInputCommand()) return;
  try {
    await handler.handle(interaction);
  } catch (error) {
    console.error('Command handling error', error);
    const content = 'Something went wrong while processing that command.';
    if (interaction.replied || interaction.deferred) {
      await interaction.followUp({ content, ephemeral: true });
    } else {
      await interaction.reply({ content, ephemeral: true });
    }
  }
});

client.login(env.discordToken).catch((error) => {
  console.error('Login failed', error);
  process.exit(1);
});
