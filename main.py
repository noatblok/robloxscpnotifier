import roblox, asyncio, os, json, aiosqlite
from dotenv import load_dotenv
from datetime import datetime
from discord_webhook import DiscordWebhook, DiscordEmbed
from roblox.utilities.iterators import SortOrder

load_dotenv()

debug = os.getenv("DEBUG")

roleview = False
memberview = False
interval = 10
webhook = DiscordWebhook(rate_limit_retry=True, url=os.getenv("DEBUG_WEBHOOK_URL") if debug else os.getenv("WEBHOOK_URL"))
opwebhook = DiscordWebhook(rate_limit_retry=True, url=os.getenv("DEBUG_WEBHOOK_URL") if debug else os.getenv("OPERATIVE_WEBHOOK_URL"))

async def main():
    client = roblox.Client(os.getenv("ROBLOX_SECURITY"))
    group = await client.get_group(os.getenv("GROUP_ID"))
    placeid = os.getenv("GAME_ID")
    db = await aiosqlite.connect("events.db")
    cur = await db.cursor()
    viplist = []

    operativelist = []

    async for member in group.get_members(sort_order=SortOrder.Ascending):
        if member.role.rank >= 250 and member.role.rank <= 253 or "task" in member.role.name.lower():
            operativelist.append(member)
        if member.role.name.lower() == "o5 command" or member.role.name.lower() == "overseer":
            viplist.append(member)

    if roleview:
        roles = await group.get_roles()
        for role in roles:
            print(f"Name: {role.name}\nRank: {role.rank}\n-----------")
    
    if memberview:
        for member in operativelist:
            print(f"Operative Name: {member.name}\nRank: {member.role.name}\n-----------")
        print("\n--------\nVIPS\n--------\n")
        for member in viplist:
            print(f"VIP Name: {member.name}\nRank: {member.role.name}\n-----------")
    print("--STARTING--")
    while True:
        with open("data.json", "r") as f:
            data = json.load(f)
        vipembeds = []
        for vip in viplist: # VIP check
            id = str(vip.id)
            if id not in data["vips"]["was_in_game"]:
                # If the vip is not in the last_seen list, add them to the list
                data["vips"]["was_in_game"][id] = False
            was_in_game = data["vips"]["was_in_game"][id]
            presence = await vip.get_presence()
            if presence.user_presence_type != roblox.presence.PresenceType.offline:
                try:
                    if presence.user_presence_type == roblox.presence.PresenceType.in_game and presence.place.id == int(placeid):
                        if was_in_game == False:
                            await cur.execute("INSERT INTO events (userid, type, timestamp) VALUES(?,?,?)", (vip.id, "join", datetime.now().timestamp(),))
                            embed = DiscordEmbed(title=f"Sign On | {vip.name}", description=f"[{vip.name}](https://www.roblox.com/users/{vip.id}/profile) has arrived on site.", color="00ff44")
                            embed.set_author(name="Notifier", url="https://www.youtube.com/watch?v=xvFZjo5PgG0", icon_url="https://i.imgur.com/4zm0lhQ.png")
                            embed.set_footer(text="*May be 10 seconds late")
                            embed.set_timestamp()
                            vipembeds.append((embed, True))
                            print(f"{vip.name} is on site.")
                        data["vips"]["was_in_game"][id] = True
                    else:
                        if was_in_game == True:
                            await cur.execute("INSERT INTO events (userid, type, timestamp) VALUES(?,?,?)", (vip.id, "leave", datetime.now().timestamp(),))
                            embed = DiscordEmbed(title=f"Sign Off | {vip.name}", description=f"[{vip.name}](https://www.roblox.com/users/{vip.id}/profile) has left the site.", color="00ff44")
                            embed.set_author(name="Notifier", url="https://www.youtube.com/watch?v=xvFZjo5PgG0", icon_url="https://i.imgur.com/4zm0lhQ.png")
                            embed.set_footer(text="*May be 10 seconds late")
                            embed.set_timestamp()
                            vipembeds.append((embed, False))
                            print(f"{vip.name} has left the site.")
                        data["vips"]["was_in_game"][id] = False
                except AttributeError as e:
                    pass
        await db.commit()
        for embed in vipembeds:
            ping = embed[1]
            webhook.add_embed(embed[0])
        if len(vipembeds) > 0:
            if ping:
                webhook.content = "<@&1092090238505070602>"
            webhook.execute(remove_embeds=True)
        opembeds = []
        for op in operativelist: # Operative check
            id = str(op.id)
            if id not in data["operatives"]["was_in_game"]:
                # If the operative is not in the last_seen list, add them to the list
                data["operatives"]["was_in_game"][id] = False
            was_in_game = data["operatives"]["was_in_game"][id]
            presence = await op.get_presence()
            if presence.user_presence_type != roblox.presence.PresenceType.offline:
                try:
                    if presence.user_presence_type == roblox.presence.PresenceType.in_game and presence.place.id == int(placeid):
                        if was_in_game == False:
                            await cur.execute("INSERT INTO events_operatives (userid, type, timestamp) VALUES(?,?,?)", (op.id, "join", datetime.now().timestamp(),))
                            embed = DiscordEmbed(title=f"Sign On | {op.name}", description=f"[{op.name}](https://www.roblox.com/users/{op.id}/profile) has arrived on site.", color="00ff44")
                            embed.set_author(name="Notifier", url="https://www.youtube.com/watch?v=xvFZjo5PgG0", icon_url="https://i.imgur.com/4zm0lhQ.png")
                            embed.set_footer(text="*May be 10 seconds late")
                            embed.set_timestamp()
                            opembeds.append(embed)
                            print(f"{op.name} is on site.")
                        data["operatives"]["was_in_game"][id] = True
                    else:
                        if was_in_game == True:
                            await cur.execute("INSERT INTO events_operatives (userid, type, timestamp) VALUES(?,?,?)", (op.id, "leave", datetime.now().timestamp(),))
                            embed = DiscordEmbed(title=f"Sign Off | {op.name}", description=f"[{op.name}](https://www.roblox.com/users/{op.id}/profile) has left the site.", color="00ff44")
                            embed.set_author(name="Notifier", url="https://www.youtube.com/watch?v=xvFZjo5PgG0", icon_url="https://i.imgur.com/4zm0lhQ.png")
                            embed.set_footer(text="*May be 10 seconds late")
                            embed.set_timestamp()
                            opembeds.append(embed)
                            print(f"{op.name} has left the site.")
                        data["operatives"]["was_in_game"][id] = False
                except AttributeError as e:
                    pass
        await db.commit()
        for embed in opembeds:
            webhook.add_embed(embed)
        if len(opembeds) > 0:
            webhook.content = "Don't mention this to anyone else. Coming soon:tm:"
            webhook.execute(remove_embeds=True)
        
        with open("data.json", "w") as f:
            json.dump(data, f, indent=4)
        await asyncio.sleep(interval)
asyncio.run(main())