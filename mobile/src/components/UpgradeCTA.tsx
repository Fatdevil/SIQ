import React from "react";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";

type UpgradeCTAProps = {
  feature: string;
  onPress: () => void;
};

const UpgradeCTA: React.FC<UpgradeCTAProps> = ({ feature, onPress }) => {
  return (
    <TouchableOpacity accessibilityRole="button" onPress={onPress} activeOpacity={0.85}>
      <View style={styles.container}>
        <Text style={styles.emoji}>🔒</Text>
        <View style={{ flex: 1 }}>
          <Text style={styles.title}>{feature} is locked</Text>
          <Text style={styles.subtitle}>Upgrade to SoccerIQ Pro to unlock this feature.</Text>
        </View>
        <Text style={styles.cta}>Upgrade</Text>
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    alignItems: "center",
    padding: 16,
    backgroundColor: "#fff7ed",
    borderRadius: 16,
    borderWidth: 1,
    borderColor: "#fed7aa",
    gap: 12
  },
  emoji: {
    fontSize: 20
  },
  title: {
    fontWeight: "600",
    color: "#9a3412",
    marginBottom: 2
  },
  subtitle: {
    color: "#ea580c"
  },
  cta: {
    fontWeight: "700",
    color: "#c2410c"
  }
});

export default UpgradeCTA;
