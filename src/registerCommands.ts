import { REST, Routes } from 'discord.js';
import { env } from './config/env';
import { commandDefinitions } from './commands/definitions';

async function register() {
  const rest = new REST({ version: '10' }).setToken(env.discordToken);
  if (env.discordGuildId) {
    await rest.put(Routes.applicationGuildCommands(env.discordClientId, env.discordGuildId), { body: commandDefinitions });
    console.log(`Registered ${commandDefinitions.length} guild commands for guild ${env.discordGuildId}`);
  } else {
    await rest.put(Routes.applicationCommands(env.discordClientId), { body: commandDefinitions });
    console.log(`Registered ${commandDefinitions.length} global commands`);
  }
}

register().catch((err) => {
  console.error('Failed to register commands', err);
  process.exit(1);
});
