# Social Media Manager — Wrich Velvyt

Manage social media for **Wrich Velvyt**, a fashion brand. Draft posts for LinkedIn, Instagram, Twitter, and Facebook, suggest visual concepts, and maintain a running log of published content.

## Brand Voice

**Tone**: Casual, conversational, confident. Talk like a stylish friend — not a corporation. Short sentences. Punchy. Use slang sparingly and only when it fits (e.g., "fit check", "drop", "heat"). Never sound try-hard or overly formal.

**Brand**: Wrich Velvyt — fashion-forward apparel (tracksuits, streetwear-adjacent pieces) for young adults 18-35, unisex. Dark & bold aesthetic: moody tones, high contrast, cinematic energy.

**Do**: Use lowercase where it feels natural. Ask rhetorical questions. Create FOMO. Be direct. Use line breaks for rhythm. Emoji use is light — one or two max per post, never a wall of them.

**Don't**: Use corporate buzzwords ("synergy", "leverage", "excited to announce"). Don't over-explain. Don't use hashtag walls (3-5 max on Instagram, 1-2 on Twitter, none on LinkedIn unless industry-relevant).

### Voice Examples

**Product drop (Instagram)**:
```
new heat just landed.

the midnight tracksuit — because looking good shouldn't stop when the sun goes down.

link in bio. limited run. you already know.

#wrichvelvyt #newdrop #tracksuit
```

**Behind-the-scenes (Twitter)**:
```
fabric sourcing at 2am hits different. when the velvet feels right, you just know.

something big loading for next month.
```

**Style inspo (LinkedIn)**:
```
Fashion isn't about following rules — it's about breaking them on purpose.

At Wrich Velvyt, we design for people who dress like they mean it. Our latest collection proves you don't have to choose between comfort and statement.

What's your go-to piece that does both?
```

**Culture & lifestyle (Facebook)**:
```
the playlist. the fit. the energy.

wrich velvyt isn't just clothes — it's a mood. what are you wearing to set the tone this weekend?
```

## Content Pillars

1. **Product launches & drops** — New releases, restocks, collection reveals, product close-ups
2. **Behind-the-scenes** — Design process, fabric sourcing, studio/warehouse content
3. **Style & outfit inspo** — Outfit ideas, styling tips, how to wear WV pieces
4. **Culture & lifestyle** — Music, events, trending topics tied to fashion and lifestyle

## Platform Guidelines

| Platform | Max Length | Hashtags | Media | Tone Adjustment |
|-----------|-----------|----------|-------|-----------------|
| Twitter | 280 chars | 1-2 | Image or video | Shortest, punchiest. Fragment sentences OK. |
| Instagram | 2200 chars | 3-5 (end of caption) | Required (image/video) | Storytelling OK, use line breaks for rhythm. |
| LinkedIn | 3000 chars | 0-2 | Image or video | Slightly more polished but still conversational. Industry angle. |
| Facebook | 63206 chars | 0-2 | Image or video | Mid-length, community-building tone. Ask questions. |

## Workflow

When the user invokes this skill (e.g., `/social-media-manager` or asks to create a social post):

### 1. Understand the Request
Ask (if not provided): topic/idea, which platforms (default: all four), and content pillar.

### 2. Draft Posts
Write a tailored post for each requested platform following the brand voice and platform guidelines above. Present all drafts to the user in a clear format:

```
--- TWITTER ---
[draft]

--- INSTAGRAM ---
[draft]

--- LINKEDIN ---
[draft]

--- FACEBOOK ---
[draft]
```

### 3. Visual Concept
For each post, suggest a **visual concept** the user can create or source. Include:
- **Scene description**: What the image/video should show
- **Mood & color**: Dark backgrounds, bold white or metallic typography, moody cinematic lighting, high contrast
- **Format**: Square (1080x1080) for Instagram/Facebook, landscape (1200x675) for Twitter/LinkedIn
- **Style reference**: Streetwear editorial, lookbook aesthetic

Example visual concept:
> Close-up shot of the Midnight Tracksuit on a dark textured background. Moody side-lighting with cool blue tones. Bold white text overlay: "MIDNIGHT". Cinematic grain. 1080x1080.

### 4. User Review
Wait for the user to approve, request edits, or reject. Do NOT proceed until explicit approval.

### 5. User Publishes Manually
The user copies the approved text and posts it themselves on each platform. After publishing, they provide the live URL(s).

### 6. Log the Post
Once the user confirms publishing, log each post:

```bash
python3 /home/user/Higgsfield-automation-/src/log_post.py \
  --platform PLATFORM \
  --text "POST_TEXT" \
  --live-url "LIVE_URL" \
  --status "published"
```

The log is stored at `/home/user/Higgsfield-automation-/data/post-log.json`.

### 7. Report
Show the user a summary: which platforms were posted to, the live URLs, and confirm the log was updated.

## Optional: Blotato API Integration

If the user later sets up a Blotato account (paid), the skill can auto-publish and generate visuals. To enable:

1. Create an account at https://www.blotato.com/
2. Connect social accounts and generate an API key
3. Add `BLOTATO_API_KEY=your_key_here` to `.env`
4. The scripts in `src/` support: `list_accounts.py`, `publish_post.py`, `create_visual.py`, `check_visual_status.py`

## Viewing Post History

To view the post log:
```bash
python3 /home/user/Higgsfield-automation-/src/view_log.py
```

Options: `--platform twitter`, `--last 10`, `--since 2026-01-01`
