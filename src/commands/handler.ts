import fs from 'node:fs';
import path from 'node:path';
import { AttachmentBuilder, ChatInputCommandInteraction, GuildMember, PermissionFlagsBits } from 'discord.js';
import { GuildSettingsRepository } from '../repositories/guildSettingsRepository';
import { UserRepository } from '../repositories/userRepository';
import { CatchRepository } from '../repositories/catchRepository';
import { CooldownRepository } from '../repositories/cooldownRepository';
import { CatalogService } from '../services/catalogService';
import { FishingService } from '../services/fishingService';
import { CooldownService } from '../services/cooldownService';
import { QuestService } from '../services/questService';
import { en } from '../i18n/en';
import { fishCatalogSchema } from '../utils/schema';

const guildSettingsRepo = new GuildSettingsRepository();
const userRepo = new UserRepository();
const catchRepo = new CatchRepository();
const cooldownService = new CooldownService(new CooldownRepository());

export class CommandHandler {
  private fishing: FishingService;
  private quests: QuestService;

  constructor(private catalog: CatalogService) {
    this.fishing = new FishingService(catalog, catchRepo, userRepo);
    this.quests = new QuestService(catalog);
  }

  async handle(interaction: ChatInputCommandInteraction) {
    if (!interaction.guildId) {
      await interaction.reply({ content: en.errors.guildOnly, ephemeral: true });
      return;
    }

    const settings = guildSettingsRepo.ensure(interaction.guildId);
    const command = interaction.commandName;

    if (command === 'fish' || command === 'fishsea') {
      const commandType = command === 'fish' ? 'fresh' : 'salt';
      const cooldown = cooldownService.check(interaction.guildId, interaction.user.id, commandType, settings.cooldown_seconds);
      if (!cooldown.allowed) {
        await interaction.reply({ content: en.fishing.cooldown(Math.ceil(cooldown.remainingMs / 1000)), ephemeral: true });
        return;
      }

      const outcome = this.fishing.fish(
        interaction.guildId,
        interaction.user.id,
        command === 'fish' ? 'fresh' : 'salt',
        settings.rewards_mode,
        settings.trinkets_enabled === 1
      );

      const valueText = settings.rewards_mode === 'coins' ? `\n💰 Value: ${outcome.value} coins` : '';
      const trinketText = outcome.trinket
        ? `\n${en.fishing.trinketFound} ${outcome.trinket.name} — ${outcome.trinket.flavor}${outcome.trinket.value ? ` (+${outcome.trinket.value} coins)` : ''}`
        : '';
      await interaction.reply(`${en.fishing.caught} **${outcome.fish.name}** (${outcome.fish.rarity})\n📏 ${outcome.length} cm • ⚖️ ${outcome.weight} kg${valueText}\n📝 ${outcome.fish.flavor[Math.floor(Math.random() * outcome.fish.flavor.length)]}${trinketText}`);
      return;
    }

    if (command === 'fishdex') {
      const showAll = interaction.options.getBoolean('all') ?? false;
      if (showAll) {
        if (!this.hasManageGuild(interaction.member)) {
          await interaction.reply({ content: en.errors.adminOnly, ephemeral: true });
          return;
        }
        const names = this.catalog.fish.map((f) => `• ${f.name} (${f.water}/${f.rarity})`).join('\n');
        await interaction.reply(`📚 Full Fish Catalog (${this.catalog.fish.length})\n${names.slice(0, 3900)}`);
        return;
      }

      const discovered = new Set(catchRepo.getDiscoveredFish(interaction.guildId, interaction.user.id));
      const discoveredFish = this.catalog.fish.filter((f) => discovered.has(f.id));
      if (discoveredFish.length === 0) {
        await interaction.reply('No fish discovered yet. Cast `/fish` or `/fishsea` first.');
        return;
      }
      const pageSize = 15;
      const page = 1;
      const entries = discoveredFish.slice((page - 1) * pageSize, page * pageSize).map((f) => `• ${f.name} (${f.water}/${f.rarity})`).join('\n');
      await interaction.reply(`🐟 Fishdex (${discoveredFish.length}/${this.catalog.fish.length})\n${entries}`);
      return;
    }

    if (command === 'sell') {
      const id = interaction.options.getInteger('catch_id') ?? userRepo.getLastFishId(interaction.user.id, interaction.guildId);
      if (!id) {
        await interaction.reply({ content: 'No recent catch found to sell.', ephemeral: true });
        return;
      }
      const catchRow = catchRepo.getCatchById(id);
      if (!catchRow || catchRow.user_id !== interaction.user.id || catchRow.guild_id !== interaction.guildId) {
        await interaction.reply({ content: 'Catch not found for this user/guild.', ephemeral: true });
        return;
      }
      if (settings.rewards_mode !== 'coins') {
        await interaction.reply({ content: 'Selling is disabled unless rewards mode is `coins`.', ephemeral: true });
        return;
      }
      const sold = catchRepo.sellCatch(id);
      if (!sold) {
        await interaction.reply({ content: 'That catch was already sold.', ephemeral: true });
        return;
      }
      userRepo.addCoins(interaction.user.id, interaction.guildId, catchRow.value);
      await interaction.reply(`Sold catch #${id} for ${catchRow.value} coins.`);
      return;
    }

    if (command === 'inventory') {
      const totalFish = catchRepo.countUserCatches(interaction.guildId, interaction.user.id);
      const trinkets = catchRepo.listUserTrinkets(interaction.guildId, interaction.user.id);
      const coins = userRepo.getCoins(interaction.user.id, interaction.guildId);
      const trinketPreview = trinkets.slice(0, 5).map((t) => `• ${t.trinket_text}${t.value ? ` (${t.value}c)` : ''}`).join('\n') || 'None';
      await interaction.reply(`🎒 Inventory\n🐟 Fish caught: ${totalFish}\n🪙 Coins: ${coins}\n🧿 Trinkets (${trinkets.length}):\n${trinketPreview}`);
      return;
    }

    if (command === 'quest') {
      if (!settings.quest_enabled) {
        await interaction.reply({ content: 'Quests are disabled on this server.', ephemeral: true });
        return;
      }
      const quest = this.quests.createQuest(interaction.guildId, interaction.user.id, settings.quest_deadline_hours);
      const lines = quest.targets.map((t) => `• ${t.quantity}x ${t.fishName}`).join('\n');
      await interaction.reply(`📜 New Quest\n${lines}\n💰 Payout: ${quest.payout} coins\n⏱️ Deadline: <t:${Math.floor(quest.deadlineAt / 1000)}:R>`);
      return;
    }

    if (command === 'admin') {
      if (!this.hasManageGuild(interaction.member)) {
        await interaction.reply({ content: en.errors.adminOnly, ephemeral: true });
        return;
      }
      const sub = interaction.options.getSubcommand();

      if (sub === 'setcooldown') {
        const seconds = interaction.options.getInteger('seconds', true);
        guildSettingsRepo.setCooldown(interaction.guildId, seconds);
        await interaction.reply(`Cooldown updated to ${seconds}s.`);
        return;
      }
      if (sub === 'togglerewards') {
        const mode = interaction.options.getString('mode', true) as 'off' | 'flavor' | 'coins';
        guildSettingsRepo.setRewardsMode(interaction.guildId, mode);
        await interaction.reply(`Rewards mode set to ${mode}.`);
        return;
      }
      if (sub === 'toggletrinkets') {
        const enabled = interaction.options.getString('enabled', true) === 'on';
        guildSettingsRepo.setTrinketsEnabled(interaction.guildId, enabled);
        await interaction.reply(`Trinkets ${enabled ? 'enabled' : 'disabled'}.`);
        return;
      }
      if (sub === 'importfish') {
        const attachment = interaction.options.getAttachment('file', true);
        const response = await fetch(attachment.url);
        const payload = await response.json();
        const parsed = fishCatalogSchema.safeParse(payload);
        if (!parsed.success) {
          const msg = parsed.error.issues.slice(0, 3).map((i) => `${i.path.join('.')}: ${i.message}`).join('; ');
          await interaction.reply({ content: `Invalid fish JSON: ${msg}`, ephemeral: true });
          return;
        }
        fs.writeFileSync(path.join(process.cwd(), 'data/fish.json'), JSON.stringify(parsed.data, null, 2));
        this.catalog.load();
        await interaction.reply(`Imported ${parsed.data.length} fish entries successfully.`);
        return;
      }
      if (sub === 'exportfish') {
        const filePath = path.join(process.cwd(), 'data/fish.json');
        const attachment = new AttachmentBuilder(filePath);
        await interaction.reply({ files: [attachment] });
      }
    }
  }

  private hasManageGuild(member: GuildMember | null): boolean {
    if (!member) return false;
    return member.permissions.has(PermissionFlagsBits.ManageGuild);
  }
}
