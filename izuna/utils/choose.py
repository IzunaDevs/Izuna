
async def choice(ctx, opts, msg):
    resp = await ctx.bot.wait_for("message", author=ctx.author, channel=ctx.channel, timeout=10)

    await msg.delete()

    if resp is None:
        await ctx.send("Please select a valid option, desu~")

    else:
        return opts[resp.content.strip()]
