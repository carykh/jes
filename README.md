# Jelly Evolution Simulator

To run this program, run this command:

```
cmd python jes.py
```

NOTE: This project, like all my projects, are not meant to be consumer products with perfect QA. Rather, it's just me, as one person, coding a casual experiment to the point that it works well enough on my computer to make a video from it! No more, no less. (I used to not put my code online, just like when you create a Minecraft world with your friends, you don't have to share the world with everyone. I just started posting code here because I wanted to make it easier for eager devs to make mods.) Long story short, I won't be doing bug-fixing or tech support on this project.

# Key-controls

X: Toggle whether or not X's show up over killed jellies

S: Store the species you're highlighting in memory. (Press S a 2nd time to unstore.) Why do this? Well, say you notice there's a creature who got #1 in a certain generation, but you can't find any trace of it elsewhere. Now, you can highlight the creature, press S, and their species bubble will show up in the upper-left. Then, roll your mouse 
over the species bubble, and there's all the species info!

C: Change the color of the species you're highlighting. Do this when 2 species are annoyingly close in color, and you want a better way to tell them apart.

Q: Open/close the creature mosaic (can also be done by clicking "Show creatures" button)

LEFT/RIGHT: Scroll through forward/backward through the timeline (can also be done by scrolling the scroll bar)

# Updates (2025-01-11)

-Mutation-finding-bug fixed (I think)

There used to be a bug where, late in the simulation, big mutations would take forever to find. That has been resolved. (It was the 0.5+ rigidity-forcing)

-Added all those key controls

-Allowed the user to change the number of creatures in the simulation (first user input)

-Fixed but where, when you click "Watch sample", it ONLY shows you a sampling of 8 creatures from the recent-est generation. Now, it always shows you a sampling of the generation your scroll bar is currently at.
