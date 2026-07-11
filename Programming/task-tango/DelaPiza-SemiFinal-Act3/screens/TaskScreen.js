import React, { useState, useRef } from "react";
import {
  KeyboardAvoidingView,
  StyleSheet,
  Text,
  View,
  Image,
  TextInput,
  TouchableOpacity,
  Platform,
  Keyboard,
  ScrollView,
  Animated,
  PanResponder,
} from "react-native";
import Task from "../components/Task";

export default function Tasks() {
  const [task, setTask] = useState("");
  const [taskItems, setTaskItems] = useState([]);
  const [isWritingTask, setIsWritingTask] = useState(false);
  const pan = useRef(new Animated.ValueXY()).current;
  const panResponder = useRef(
    PanResponder.create({
      onStartShouldSetPanResponder: () => true,
      onPanResponderMove: Animated.event([null, { dx: pan.x, dy: pan.y }], {
        useNativeDriver: false,
      }),
      onPanResponderRelease: () => {
        Animated.spring(pan, {
          toValue: { x: 0, y: 0 },
          useNativeDriver: false,
        }).start();
      },
    })
  ).current;

  const handleAddTask = () => {
    const trimmedTask = task.trim();
    if (!trimmedTask) return;

    Keyboard.dismiss();
    setTaskItems((currentItems) => [...currentItems, trimmedTask]);
    setTask("");
    setIsWritingTask(false);
  };

  const completeTask = (index) => {
    let itemsCopy = [...taskItems];
    itemsCopy.splice(index, 1);
    setTaskItems(itemsCopy);
  };

  const startWritingTask = () => {
    setIsWritingTask(true);
  };

  const finishWritingTask = () => {
    setIsWritingTask(false);
  };

  return (
    <View style={styles.container}>
      <ScrollView
        contentContainerStyle={{
          flexGrow: 1,
        }}
        keyboardShouldPersistTaps="handled"
      >
        {/* Today's Tasks */}
        <View style={styles.tasksWrapper}>
          <Animated.View
            style={{
              transform: [{ translateX: pan.x }, { translateY: pan.y }],
            }}
            {...panResponder.panHandlers}
          >
            <Image source={require("../checklist.png")} style={styles.logo} />
          </Animated.View>
          <Text style={styles.sectionTitle}>to-do</Text>
          {isWritingTask ? null : (
            <View style={styles.items}>
              {/* This is where the tasks will go! */}
              {taskItems.map((item, index) => {
                return (
                  <TouchableOpacity
                    key={index}
                    onPress={() => completeTask(index)}
                  >
                    <Task text={item} onComplete={() => completeTask(index)} />
                  </TouchableOpacity>
                );
              })}
            </View>
          )}
        </View>
      </ScrollView>

      <KeyboardAvoidingView
        behavior={Platform.OS === "ios" ? "padding" : "height"}
        style={styles.writeTaskWrapper}
      >
        {isWritingTask ? (
          <TextInput
            style={styles.input}
            placeholder={"Write a task"}
            value={task}
            onChangeText={(text) => setTask(text)}
            onBlur={finishWritingTask}
          />
        ) : (
          <TouchableOpacity onPress={startWritingTask}>
            <Text style={styles.placeholder}>Add a task...</Text>
          </TouchableOpacity>
        )}

        {isWritingTask ? (
          <TouchableOpacity onPress={handleAddTask}>
            <View style={styles.addWrapper}>
              <Text style={styles.addText}>+</Text>
            </View>
          </TouchableOpacity>
        ) : null}
      </KeyboardAvoidingView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#FFF",
  },
  logo: {
    width: 100,
    height: 100,
    marginBottom: 10,
    alignSelf: "center",
  },
  tasksWrapper: {
    paddingTop: 80,
    paddingHorizontal: 20,
  },
  sectionTitle: {
    fontSize: 30,
    fontWeight: "bold",
    color: "black",
    marginBottom: 20,
    textAlign: "center",
  },
  items: {
    marginTop: 10,
  },
  writeTaskWrapper: {
    position: "absolute",
    bottom: 60,
    width: "100%",
    flexDirection: "row",
    justifyContent: "space-around",
    alignItems: "center",
    paddingHorizontal: 20,
  },
  input: {
    flex: 1,
    paddingVertical: 15,
    paddingHorizontal: 15,
    borderColor: "#C0C0C0",
    borderRadius: 60,
    borderWidth: 1,
    color: "black",
  },
  placeholder: {
    paddingVertical: 15,
    paddingHorizontal: 15,
    borderColor: "#C0C0C0",
    borderRadius: 60,
    borderWidth: 1,
    color: "#C0C0C0",
  },
  addWrapper: {
    width: 50,
    height: 50,
    borderRadius: 50,
    backgroundColor: "#007BFF",
    justifyContent: "center",
    alignItems: "center",
  },
  addText: {
    fontSize: 30,
    color: "white",
  },
});
