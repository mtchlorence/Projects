import React, { useState } from "react";
import {
  View,
  Text,
  TextInput,
  StyleSheet,
  Alert,
} from "react-native";
import { StatusBar } from "expo-status-bar";
import Button from "./components/Button";
import { FontAwesomeIcon } from "@fortawesome/react-native-fontawesome";
import {
  faEnvelope,
  faLock,
  faUser,
} from "@fortawesome/free-solid-svg-icons";

export default function SignUpScreen() {
  const [name, setName] = useState("");
  const [emailAddress, setEmailAddress] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const handleSignUp = () => {
    // Validation
    if (!name || !emailAddress || !password || !confirmPassword) {
      showAlert("All fields are required");
      return;
    }
    if (password !== confirmPassword) {
      showAlert("Passwords do not match");
      return;
    }

    showAlert("Sign Up Successful", `Name: ${name}\nEmail: ${emailAddress}`);
  };

  const showAlert = (title, message) => {
    Alert.alert(
      title,
      message,
      [{ text: "OK", onPress: () => console.log("OK Pressed") }],
      { cancelable: false }
    );
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Sign Up</Text>
      <View style={styles.inputContainer}>
        <FontAwesomeIcon icon={faUser} size={20} color="white" style={styles.icon} />
        <TextInput
          style={styles.input}
          onChangeText={setName}
          value={name}
          placeholder="Enter name"
          placeholderTextColor="white"
        />
      </View>
      <View style={styles.inputContainer}>
        <FontAwesomeIcon icon={faEnvelope} size={20} color="white" style={styles.icon} />
        <TextInput
          style={styles.input}
          onChangeText={setEmailAddress}
          value={emailAddress}
          placeholder="Enter email"
          placeholderTextColor="white"
        />
      </View>
      <View style={styles.inputContainer}>
        <FontAwesomeIcon icon={faLock} size={20} color="white" style={styles.icon} />
        <TextInput
          style={styles.input}
          onChangeText={setPassword}
          value={password}
          placeholder="Enter password"
          secureTextEntry={true} // Mask the password input
          placeholderTextColor="white"
        />
      </View>
      <View style={styles.inputContainer}>
        <FontAwesomeIcon icon={faLock} size={20} color="white" style={styles.icon} />
        <TextInput
          style={styles.input}
          onChangeText={setConfirmPassword}
          value={confirmPassword}
          placeholder="Confirm password"
          secureTextEntry={true} // Mask the password input
          placeholderTextColor="white"
        />
      </View>
      <View style={styles.inputContainer}>
        <Text style={styles.policyText}>
          By signing up, you agree to our Terms, Data Policy and Cookies Policy.
        </Text>
      </View>
      <Button
        title="Create Account"
        filled
        style={styles.button}
        onPress={handleSignUp}
      />
      <StatusBar style="auto" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "black",
    opacity: 0.9,
    alignItems: "center",
    justifyContent: "center",
  },
  title: {
    color: "white",
    fontSize: 45,
    marginBottom: 24,
    fontWeight: "bold",
  },
  inputContainer: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    width: "65%",
  },
  input: {
    height: 50,
    margin: 12,
    width: "100%",
    padding: 10,
    borderWidth: 1,
    borderRadius: 5,
    color: "white",
    borderColor: "white",
  },
  icon: {
    marginRight: 10,
  },
  button: {
    marginTop: 18,
    marginBottom: 4,
  },
  policyText: {
    color: "white",
    textAlign: "center",
    width: "100%",
    marginBottom: 12,
  },
});
