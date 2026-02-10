import { PermissionFlagsBits, SlashCommandBuilder } from 'discord.js';

export const commandDefinitions = [
  new SlashCommandBuilder().setName('fish').setDescription('Catch a freshwater fish.'),
  new SlashCommandBuilder().setName('fishsea').setDescription('Catch a saltwater fish.'),
  new SlashCommandBuilder()
    .setName('fishdex')
    .setDescription('View discovered fish entries.')
    .addBooleanOption((o) => o.setName('all').setDescription('Show full catalog (admin only).')),
  new SlashCommandBuilder()
    .setName('sell')
    .setDescription('Sell your last catch or a specific catch id.')
    .addIntegerOption((o) => o.setName('catch_id').setDescription('Specific catch id to sell.').setRequired(false)),
  new SlashCommandBuilder().setName('inventory').setDescription('Show your fish, trinkets, and coins.'),
  new SlashCommandBuilder().setName('quest').setDescription('Generate a timed fishing quest with payout.'),
  new SlashCommandBuilder()
    .setName('admin')
    .setDescription('Admin settings for fishing bot.')
    .setDefaultMemberPermissions(PermissionFlagsBits.ManageGuild)
    .addSubcommand((s) => s.setName('setcooldown').setDescription('Set /fish cooldown in seconds.').addIntegerOption((o) => o.setName('seconds').setRequired(true).setMinValue(1).setMaxValue(3600).setDescription('Cooldown seconds.')))
    .addSubcommand((s) => s.setName('togglerewards').setDescription('Set rewards mode.').addStringOption((o) => o.setName('mode').setDescription('off/flavor/coins').setRequired(true).addChoices({ name: 'off', value: 'off' }, { name: 'flavor', value: 'flavor' }, { name: 'coins', value: 'coins' })))
    .addSubcommand((s) => s.setName('toggletrinkets').setDescription('Enable/disable trinkets.').addStringOption((o) => o.setName('enabled').setDescription('on/off').setRequired(true).addChoices({ name: 'on', value: 'on' }, { name: 'off', value: 'off' })))
    .addSubcommand((s) => s.setName('importfish').setDescription('Import fish catalog from attached JSON.').addAttachmentOption((o) => o.setName('file').setRequired(true).setDescription('Fish JSON file.')))
    .addSubcommand((s) => s.setName('exportfish').setDescription('Export current fish catalog JSON.'))
].map((c) => c.toJSON());
