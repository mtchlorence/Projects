import React from "react";
import { View, Text, StyleSheet, Image, TouchableOpacity } from "react-native";
import { useNavigation } from "@react-navigation/native";

export default function Home() {
  const navigation = useNavigation();
  return (
    <View style={styles.container}>
      <Text style={styles.appTitle}>TaskTango</Text>
      <View style={styles.logoContainer}>
        <Image source={require("../checklist.png")} style={styles.logo} />
      </View>
      <TouchableOpacity
        style={styles.button}
        onPress={() => navigation.navigate("TaskScreen")}
      >
        <Text style={styles.buttonText}>Go to Tasks</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#FFF",
    alignItems: "center",
    justifyContent: "center",
  },
  appTitle: {
    fontSize: 40,
    fontWeight: "bold",
    color: "#000",
    marginBottom: 30,
  },
  logoContainer: {
    backgroundColor: "#F2F2F2",
    borderRadius: 75,
    padding: 10,
    marginBottom: 30,
  },
  logo: {
    height: 150,
    width: 150,
  },
  button: {
    backgroundColor: "#007BFF",
    paddingVertical: 15,
    paddingHorizontal: 40,
    borderRadius: 30,
  },
  buttonText: {
    fontSize: 18,
    color: "#FFF",
    fontWeight: "bold",
  },
});
