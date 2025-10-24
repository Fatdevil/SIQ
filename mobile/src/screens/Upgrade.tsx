import React, { useState } from "react";
import { ActivityIndicator, Alert, StyleSheet, Text, TextInput, TouchableOpacity, View } from "react-native";
import { useBilling } from "../hooks/useBilling";

const API_BASE = process.env.EXPO_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

const PLATFORMS = [
  { id: "ios", label: "iOS" },
  { id: "android", label: "Android" },
  { id: "web-mock", label: "Web mock" }
];

type UpgradeScreenProps = {
  onComplete: () => void;
};

const UpgradeScreen: React.FC<UpgradeScreenProps> = ({ onComplete }) => {
  const { userId, refresh } = useBilling();
  const [receipt, setReceipt] = useState("");
  const [platform, setPlatform] = useState("ios");
  const [submitting, setSubmitting] = useState(false);

  const submit = async () => {
    if (!receipt.trim()) {
      Alert.alert("Missing receipt", "Enter a mock receipt such as PRO-DEV or ELITE-QA.");
      return;
    }

    setSubmitting(true);

    try {
      const response = await fetch(`${API_BASE}/billing/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ userId, platform, receipt: receipt.trim() })
      });

      if (!response.ok) {
        throw new Error(`status ${response.status}`);
      }

      await refresh();
      Alert.alert("Success", "Tier updated!", [{ text: "Continue", onPress: onComplete }]);
      setReceipt("");
    } catch (error) {
      console.error(error);
      Alert.alert("Upgrade failed", "Double-check the mock receipt prefix (PRO-* or ELITE-*).");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Activate SoccerIQ Pro</Text>
      <Text style={styles.subtitle}>
        Enter a mock receipt and the client will refresh billing status instantly.
      </Text>

      <View style={styles.formGroup}>
        <Text style={styles.label}>Mock receipt</Text>
        <TextInput
          value={receipt}
          onChangeText={setReceipt}
          placeholder="PRO-DEV"
          style={styles.input}
          autoCapitalize="characters"
        />
      </View>

      <View style={styles.formGroup}>
        <Text style={styles.label}>Platform</Text>
        <View style={styles.platformRow}>
          {PLATFORMS.map((item) => {
            const active = item.id === platform;
            return (
              <TouchableOpacity
                key={item.id}
                style={[styles.platformButton, active && styles.platformButtonActive]}
                onPress={() => setPlatform(item.id)}
              >
                <Text style={[styles.platformText, active && styles.platformTextActive]}>{item.label}</Text>
              </TouchableOpacity>
            );
          })}
        </View>
      </View>

      <TouchableOpacity style={styles.submitButton} onPress={submit} disabled={submitting} activeOpacity={0.85}>
        {submitting ? <ActivityIndicator color="#fff" /> : <Text style={styles.submitText}>Activate Pro</Text>}
      </TouchableOpacity>

      <View style={styles.rules}>
        <Text style={styles.ruleTitle}>Mock rules</Text>
        <Text style={styles.ruleText}>• Receipts beginning with PRO- unlock the Pro tier.</Text>
        <Text style={styles.ruleText}>• Receipts beginning with ELITE- unlock the Elite tier.</Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 24,
    gap: 16
  },
  title: {
    fontSize: 28,
    fontWeight: "700",
    color: "#0f172a"
  },
  subtitle: {
    color: "#475569"
  },
  formGroup: {
    gap: 8
  },
  label: {
    fontWeight: "600",
    color: "#1e293b"
  },
  input: {
    borderWidth: 1,
    borderColor: "#cbd5f5",
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 16,
    backgroundColor: "#fff"
  },
  platformRow: {
    flexDirection: "row",
    gap: 8
  },
  platformButton: {
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: "#cbd5f5"
  },
  platformButtonActive: {
    backgroundColor: "#2563eb",
    borderColor: "#1d4ed8"
  },
  platformText: {
    color: "#1e293b",
    fontWeight: "600"
  },
  platformTextActive: {
    color: "#fff"
  },
  submitButton: {
    backgroundColor: "#2563eb",
    borderRadius: 16,
    paddingVertical: 16,
    alignItems: "center"
  },
  submitText: {
    color: "#fff",
    fontWeight: "700",
    fontSize: 16
  },
  rules: {
    marginTop: 12,
    gap: 4
  },
  ruleTitle: {
    fontWeight: "700",
    color: "#1e293b"
  },
  ruleText: {
    color: "#475569"
  }
});

export default UpgradeScreen;
