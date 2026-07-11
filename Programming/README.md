# Programming Projects

A collection of college programming activities built with HTML, CSS, JavaScript, React Native, and Expo.

## Browser projects

These projects can be opened directly in a web browser:

- `Area-Calculator.html` — calculates the area of common shapes.
- `ASCII-Converter.html` — converts characters and ASCII values.
- `Body-Fat-Calculator.html` — estimates body-fat percentage from user input.
- `Number-Sorter.html` — sorts a list of numbers.
- `story-telling/ELEC3_DelaPiza-StoryTelling/index.html` — interactive storytelling activity.

To test a browser project, open its HTML file and use the browser's developer tools to check the Console and responsive layout.

## Expo projects

### Todo List (Activity 2)

Location: `DelaPiza-Act2/DelaPiza-Act2`

A basic React Native todo-list application where tasks can be added and removed.

### TaskTango

Location: `task-tango/DelaPiza-SemiFinal-Act3`

A React Native task application with stack navigation and an interactive task screen.

### Testing Project

Location: `TestingProject`

A React Native sign-up form with input validation and Font Awesome icons.

### Todo App

Location: `todo-app/DelaPiza-Todo/react-native-todo-app/react-native-todo-app`

A larger todo application using Redux and persistent local storage.

## Running an Expo project

Open PowerShell in the selected project directory, then run:

```powershell
npm install
npx.cmd expo-doctor
npx.cmd expo start --clear
```

Use `npx.cmd` on this Windows system because PowerShell may block the `npx.ps1` wrapper.

After Expo starts:

- Scan the QR code with Expo Go to test on a physical device.
- Press `a` to launch an Android emulator.
- Press `w` to launch the web version when supported.
- Press `Ctrl+C` to stop the development server.

## Testing checklist

- Test empty, invalid, and valid input.
- Test every button and navigation route.
- Check the terminal and browser console for errors.
- Test on both a small screen and a larger screen.
- Reload the application and confirm that saved data behaves correctly.
- Test at least once on a physical Android or iOS device.

## Compatibility note

The Expo projects currently use Expo SDK 50 or 51. They may need to be upgraded before they can run in a newer Expo Go installation.
