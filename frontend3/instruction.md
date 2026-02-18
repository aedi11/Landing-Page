# Editing Instructions for the Landing Page

This guide explains how to edit common content in the landing page located at `src/app/page.tsx`.

---

## Editing Team Members (Leadership Section)

Team member data is stored in the `teamMembers` array near line 752 in `page.tsx`.

### To edit an existing member

Find the member's object in the array and modify the fields:

```ts
{
  icon: Code,                          // Lucide icon (shown as fallback if no image)
  image: "/images/vipul.jpeg",         // Path to profile photo in public/images/
  name: "Vipul Lout",                  // Display name
  title: "Full-Stack Developer",       // Role shown on the card
  description:                         // Qualification shown when the card is expanded
    "B.Tech graduate in Electrical Engineering from Indian Institute of Technology Delhi.",
  accent: "#0E7490",                   // Accent colour for the card border/highlight
},
```

### To add a new team member

1. Place the profile photo in `public/images/` (e.g., `public/images/new_person.png`).
2. Add a new object to the `teamMembers` array following the same structure above.
3. Choose a Lucide icon from [lucide.dev/icons](https://lucide.dev/icons) and import it at the top of the file.
4. Pick an accent colour — existing ones used are:
   - `#EAC97C` (gold)
   - `#0E7490` (teal)
   - `#059669` (green)

### To remove a team member

Delete the entire object (from `{` to `},`) for that member from the `teamMembers` array.

---

## Editing Section Headings and Descriptions

Most sections follow a similar pattern:

```tsx
<h2 className="...">
  <span className="text-[#EAC97C]">The Minds Driving</span>{" "}
  <span className="text-[#0E7490]">India&apos;s</span>{" "}
  <span className="text-[#EAC97C]">Tech Sovereignty</span>
</h2>
```

Simply change the text inside the `<span>` tags. Use `&apos;` for apostrophes and `&amp;` for ampersands.

The subtitle/description text is in the `<p>` tag directly below the heading.

---

## Editing Images

All images are stored in `public/images/`. To replace an image:

1. Place the new image file in `public/images/`.
2. Update the `image` field in the relevant data array to match the new filename.
3. Supported formats: `.png`, `.jpg`, `.jpeg`, `.webp`.

---

## Accent Colours Reference

| Colour  | Hex Code  | Usage                |
| ------- | --------- | -------------------- |
| Gold    | `#EAC97C` | Primary headings     |
| Teal    | `#0E7490` | Secondary highlights |
| Green   | `#059669` | Tertiary accents     |
| Brown   | `#826015` | Background elements  |

---

## Running the Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to preview changes.
