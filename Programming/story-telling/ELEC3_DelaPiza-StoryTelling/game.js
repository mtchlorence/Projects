// Define story chapters as an array of objects
const storyChapters = [
  {
    title: "The Call to Adventure",
    content:
      "You stand at the edge of the dense jungle, a map in hand and a sense of excitement in your heart. Before you lies the entrance to the Forgotten Temple, rumored to hold secrets beyond imagination. Do you:",
    choices: [
      { text: "Follow the Main Path", nextChapter: 2 },
      { text: "Forge Your Own Path", nextChapter: 3 },
    ],
  },
  {
    title: "Into the Jungle",
    content:
      "As you journey deeper into the jungle, you encounter your first obstacle—a raging river blocking your path. Do you:",
    choices: [
      { text: "Build a Raft", nextChapter: 4 },
      { text: "Find a Crossing", nextChapter: 5 },
    ],
  },
  {
    title: "The Temple's Gate",
    content:
      "After hours of trekking through the dense foliage, you finally arrive at the entrance to the temple. Before you looms a massive stone gate adorned with mysterious symbols. Do you:",
    choices: [
      { text: "Decipher the Symbols", nextChapter: 6 },
      { text: "Search for a Hidden Entrance", nextChapter: 7 },
    ],
  },
  {
    title: "Inside the Temple",
    content:
      "You step into the dimly lit interior of the temple, greeted by an eerie silence broken only by the sound of your footsteps echoing off the ancient stone walls. Do you:",
    choices: [
      { text: "Follow the Main Corridor", nextChapter: 8 },
      { text: "Take a Side Passage", nextChapter: 9 },
    ],
  },
  {
    title: "Confronting the Guardians",
    content:
      "As you delve deeper into the temple, you encounter a group of mystical guardians tasked with protecting its secrets. Do you:",
    choices: [
      { text: "Engage in Combat", nextChapter: 10 },
      { text: "Attempt Diplomacy", nextChapter: 11 },
    ],
  },
  {
    title: "Unraveling the Mystery",
    content:
      "You stumble upon a chamber filled with ancient artifacts and inscriptions, hinting at the true purpose of the temple. Do you:",
    choices: [
      { text: "Study the Artifacts", nextChapter: 12 },
      { text: "Search for Hidden Passages", nextChapter: 13 },
    ],
  },
  {
    title: "The Final Revelation",
    content:
      "After hours of exploration and discovery, you reach the inner sanctum of the temple, where the ultimate treasure awaits. Do you:",
    choices: [
      { text: "Claim the Treasure", nextChapter: 14 },
      { text: "Leave the Treasure Untouched", nextChapter: 15 },
    ],
  },
  {
    title: "The End",
    content:
      "Congratulations, brave adventurer! Your journey through the Forgotten Temple has come to an end. Whether you claimed the treasure or left it untouched, your courage and determination have forever changed the course of your destiny.",
    choices: [],
  },
];

let currentChapterIndex = 0;

// Function to display current chapter
function displayChapter() {
  const chapter = storyChapters[currentChapterIndex];
  const storyContainer = document.getElementById("story-container");
  storyContainer.innerHTML = `
        <h2>${chapter.title}</h2>
        <p>${chapter.content}</p>
    `;

  // Display choices
  chapter.choices.forEach((choice) => {
    const choiceButton = document.createElement("button");
    choiceButton.textContent = choice.text;
    choiceButton.className = "choice-button";
    choiceButton.addEventListener("click", () =>
      goToNextChapter(choice.nextChapter)
    );
    storyContainer.appendChild(choiceButton);
  });
}

// Function to navigate to the next chapter
function goToNextChapter(nextChapterIndex) {
  currentChapterIndex = nextChapterIndex - 1;
  if (currentChapterIndex >= storyChapters.length - 1) {
    currentChapterIndex = storyChapters.length - 1; // Ensure it stays at the last chapter
  }
  displayChapter();
}

// Initial display
displayChapter();
