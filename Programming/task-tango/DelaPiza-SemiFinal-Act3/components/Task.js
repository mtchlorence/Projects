import React from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";

export default function Task({ text, onComplete }) {
  return (
    <View style={styles.item}>
      <View style={styles.itemLeft}>
        <Text style={styles.itemText}>{text}</Text>
      </View>
      <TouchableOpacity onPress={onComplete}>
        <View style={styles.checkbox}></View>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  item: {
    backgroundColor: "#FFF",
    borderRadius: 10,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 10,
    paddingVertical: 10,
    paddingHorizontal: 15,
    borderWidth: 1,
    borderColor: "#E0E0E0",
  },
  itemLeft: {
    flexDirection: "row",
    alignItems: "center",
    flexWrap: "wrap",
  },
  itemText: {
    maxWidth: "80%",
  },
  checkbox: {
    width: 24,
    height: 24,
    backgroundColor: "#55BCF6",
    borderColor: "#55BCF6",
    borderWidth: 2,
    borderRadius: 5,
  },
});
