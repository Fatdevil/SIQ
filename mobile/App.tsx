import React, { useCallback, useMemo, useState } from "react";
import {
  SafeAreaView,
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Share,
  ScrollView
} from "react-native";
import { UserProvider } from "./src/context/UserContext";
import { useBilling } from "./src/hooks/useBilling";
import UpgradeCTA from "./src/components/UpgradeCTA";
import UpgradeScreen from "./src/screens/Upgrade";

type Highlight = {
  id: string;
  title: string;
  subtitle: string;
  badge: string;
  assetPath: string;
  speed: number;
};

type LeaderboardEntry = {
  id: string;
  player: string;
  score: string;
  region: string;
};

const TABS = [
  { id: "highlights", label: "Highlights" },
  { id: "hardest", label: "Hardest Shot" },
  { id: "hits", label: "Most Hits" }
];

const highlightData: Highlight[] = [
  {
    id: "1",
    title: "Crossbar Laser",
    subtitle: "112 km/h · Left Foot",
    badge: "TOP BINS",
    assetPath: "file:///highlights/highlight-1.mp4",
    speed: 112
  },
  {
    id: "2",
    title: "Volley Rocket",
    subtitle: "108 km/h · Right Foot",
    badge: "PERSONAL BEST",
    assetPath: "file:///highlights/highlight-2.mp4",
    speed: 108
  }
];

const hardestShot: LeaderboardEntry[] = [
  { id: "h1", player: "J. Alvarez", score: "118 km/h", region: "Global" },
  { id: "h2", player: "S. Ito", score: "115 km/h", region: "Tokyo" },
  { id: "h3", player: "M. Smith", score: "113 km/h", region: "Austin" }
];

const mostHits: LeaderboardEntry[] = [
  { id: "m1", player: "J. Alvarez", score: "17 hits", region: "Global" },
  { id: "m2", player: "A. Lopes", score: "16 hits", region: "Lisbon" },
  { id: "m3", player: "K. Singh", score: "15 hits", region: "Delhi" }
];

const PERSONAS = [
  { id: "striker", name: "Striker Savant", focus: "Finishing + volley drills" },
  { id: "maestro", name: "Midfield Maestro", focus: "Tempo and possession" },
  { id: "wall", name: "Backline Wall", focus: "Press resistance + clearances" }
];

function useShareHandler() {
  return useCallback(async (highlight: Highlight) => {
    await Share.share({
      title: highlight.title,
      message: `${highlight.title} — ${highlight.speed} km/h`,
      url: highlight.assetPath
    });
  }, []);
}

const PersonaRow: React.FC<{ persona: (typeof PERSONAS)[number]; locked: boolean }> = ({ persona, locked }) => {
  return (
    <View style={[styles.personaCard, locked && styles.personaCardLocked]}>
      <Text style={styles.personaTitle}>{persona.name}</Text>
      <Text style={styles.personaSubtitle}>{persona.focus}</Text>
      {locked ? <Text style={styles.personaLocked}>Locked</Text> : null}
    </View>
  );
};

const HomeScreen: React.FC<{ onUpgrade: () => void }> = ({ onUpgrade }) => {
  const [tab, setTab] = useState<string>("highlights");
  const onShare = useShareHandler();
  const { status, loading, refresh, isElite, isPro, canUse } = useBilling();

  const tierLabel = useMemo(() => {
    switch (status?.tier) {
      case "elite":
        return "Elite";
      case "pro":
        return "Pro";
      default:
        return "Free";
    }
  }, [status?.tier]);

  const personaUnlocked = canUse("AI_PERSONAS");
  const arUnlocked = canUse("ADVANCED_METRICS");
  const visiblePersonas = personaUnlocked ? PERSONAS : PERSONAS.slice(0, 1);

  const leaderboardContent = useMemo(() => {
    if (tab === "hardest") {
      return <LeaderboardList title="Hardest Shot — 7 Days" data={hardestShot} />;
    }
    if (tab === "hits") {
      return <LeaderboardList title="Most Hits — 7 Days" data={mostHits} />;
    }
    return null;
  }, [tab]);

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <Text style={styles.header}>SoccerIQ Mobile Studio</Text>
        <View style={styles.statusCard}>
          <View style={styles.statusRow}>
            <View
              style={[
                styles.statusPill,
                isElite ? styles.statusPillElite : isPro ? styles.statusPillPro : undefined
              ]}
            >
              <Text style={styles.statusPillText}>Tier: {tierLabel}</Text>
            </View>
            <TouchableOpacity
              accessibilityRole="button"
              style={[styles.refreshButton, loading && styles.refreshButtonDisabled]}
              onPress={() => refresh()}
              disabled={loading}
            >
              <Text style={styles.refreshButtonText}>{loading ? "Refreshing…" : "Refresh status"}</Text>
            </TouchableOpacity>
          </View>
          <Text style={styles.statusHelp}>
            Try mock receipts like <Text style={styles.statusHelpStrong}>PRO-DEV</Text> or
            <Text style={styles.statusHelpStrong}> ELITE-QA</Text> from the Upgrade screen.
          </Text>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Coach personas</Text>
          <Text style={styles.sectionSubtitle}>
            Tailored AI coaches that adapt training plans. Free tier includes one persona.
          </Text>
          <View style={styles.personaRow}>
            {visiblePersonas.map((persona, index) => (
              <PersonaRow key={persona.id} persona={persona} locked={!personaUnlocked && index > 0} />
            ))}
          </View>
          {!personaUnlocked ? <UpgradeCTA feature="Coach personas" onPress={onUpgrade} /> : null}
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>AR Target precision scoring</Text>
          <Text style={styles.sectionSubtitle}>
            Visual overlays analyse shot placement and adapt drills to your form.
          </Text>
          {arUnlocked ? (
            <View style={styles.arCard}>
              <Text style={styles.arLine}>Precision: 87% inside target zones</Text>
              <Text style={styles.arLine}>Adaptive mode queued 3 drills for tomorrow</Text>
              <Text style={styles.arLine}>Elite bonus: academy leaderboard unlocked</Text>
            </View>
          ) : (
            <UpgradeCTA feature="AR Target precision scoring" onPress={onUpgrade} />
          )}
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Highlights & Leaderboards</Text>
          <View style={styles.tabBar}>
            {TABS.map((tabItem) => (
              <TabButton key={tabItem.id} {...tabItem} active={tabItem.id === tab} onPress={setTab} />
            ))}
          </View>
          {tab === "highlights" ? (
            <View style={styles.highlightList}>
              {highlightData.map((highlight) => (
                <HighlightCard key={highlight.id} highlight={highlight} onShare={onShare} />
              ))}
            </View>
          ) : (
            <View style={styles.leaderboardContainer}>{leaderboardContent}</View>
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const LeaderboardList: React.FC<{ title: string; data: LeaderboardEntry[] }> = ({ title, data }) => (
  <View style={styles.leaderboardCard}>
    <Text style={styles.leaderboardTitle}>{title}</Text>
    {data.map((entry, index) => (
      <View key={entry.id} style={styles.leaderboardRow}>
        <Text style={styles.leaderboardRank}>{index + 1}</Text>
        <View style={styles.leaderboardInfo}>
          <Text style={styles.leaderboardPlayer}>{entry.player}</Text>
          <Text style={styles.leaderboardRegion}>{entry.region}</Text>
        </View>
        <Text style={styles.leaderboardScore}>{entry.score}</Text>
      </View>
    ))}
  </View>
);

const TabButton: React.FC<{
  id: string;
  label: string;
  active: boolean;
  onPress: (id: string) => void;
}> = ({ id, label, active, onPress }) => {
  return (
    <TouchableOpacity
      accessibilityRole="button"
      style={[styles.tabButton, active && styles.tabButtonActive]}
      onPress={() => onPress(id)}
    >
      <Text style={[styles.tabButtonText, active && styles.tabButtonTextActive]}>{label}</Text>
    </TouchableOpacity>
  );
};

const HighlightCard: React.FC<{ highlight: Highlight; onShare: (highlight: Highlight) => void }> = ({
  highlight,
  onShare
}) => (
  <View style={styles.highlightCard}>
    <View style={styles.highlightPreview}>
      <Text style={styles.highlightBadge}>{highlight.badge}</Text>
    </View>
    <View style={styles.highlightDetails}>
      <Text style={styles.highlightTitle}>{highlight.title}</Text>
      <Text style={styles.highlightSubtitle}>{highlight.subtitle}</Text>
      <TouchableOpacity
        accessibilityLabel={`Share ${highlight.title}`}
        style={styles.shareButton}
        onPress={() => onShare(highlight)}
      >
        <Text style={styles.shareButtonText}>Share</Text>
      </TouchableOpacity>
    </View>
  </View>
);

const Root: React.FC = () => {
  const [screen, setScreen] = useState<"home" | "upgrade">("home");

  if (screen === "upgrade") {
    return (
      <SafeAreaView style={styles.lightContainer}>
        <UpgradeScreen onComplete={() => setScreen("home")} />
      </SafeAreaView>
    );
  }

  return <HomeScreen onUpgrade={() => setScreen("upgrade")} />;
};

const App: React.FC = () => {
  return (
    <UserProvider>
      <Root />
    </UserProvider>
  );
};

export default App;

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0c1524"
  },
  lightContainer: {
    flex: 1,
    backgroundColor: "#f8fafc"
  },
  scrollContent: {
    paddingHorizontal: 16,
    paddingBottom: 32,
    gap: 24
  },
  header: {
    fontSize: 24,
    fontWeight: "700",
    color: "#ffffff",
    marginTop: 16
  },
  statusCard: {
    backgroundColor: "rgba(255,255,255,0.08)",
    borderRadius: 20,
    padding: 16,
    gap: 12
  },
  statusRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center"
  },
  statusPill: {
    paddingHorizontal: 16,
    paddingVertical: 6,
    borderRadius: 999,
    backgroundColor: "rgba(14,165,233,0.2)"
  },
  statusPillText: {
    color: "#38bdf8",
    fontWeight: "600"
  },
  statusPillPro: {
    backgroundColor: "rgba(34,197,94,0.2)"
  },
  statusPillElite: {
    backgroundColor: "rgba(236,72,153,0.2)"
  },
  refreshButton: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 12,
    backgroundColor: "#00d1ff"
  },
  refreshButtonDisabled: {
    opacity: 0.6
  },
  refreshButtonText: {
    fontWeight: "700",
    color: "#001021"
  },
  statusHelp: {
    color: "rgba(255,255,255,0.7)"
  },
  statusHelpStrong: {
    fontWeight: "700",
    color: "#ffffff"
  },
  section: {
    backgroundColor: "rgba(255,255,255,0.08)",
    borderRadius: 20,
    padding: 16,
    gap: 16
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: "#ffffff"
  },
  sectionSubtitle: {
    color: "rgba(255,255,255,0.75)"
  },
  personaRow: {
    flexDirection: "row",
    gap: 12,
    flexWrap: "wrap"
  },
  personaCard: {
    flexBasis: "48%",
    backgroundColor: "rgba(12,21,36,0.6)",
    borderRadius: 16,
    padding: 12,
    borderWidth: 1,
    borderColor: "rgba(148,163,184,0.3)"
  },
  personaCardLocked: {
    opacity: 0.6
  },
  personaTitle: {
    color: "#ffffff",
    fontWeight: "700",
    marginBottom: 4
  },
  personaSubtitle: {
    color: "rgba(255,255,255,0.7)"
  },
  personaLocked: {
    marginTop: 8,
    color: "#f97316",
    fontWeight: "600"
  },
  arCard: {
    backgroundColor: "rgba(12,21,36,0.6)",
    borderRadius: 16,
    padding: 16,
    gap: 8,
    borderWidth: 1,
    borderColor: "rgba(148,163,184,0.3)"
  },
  arLine: {
    color: "#ffffff"
  },
  tabBar: {
    flexDirection: "row",
    justifyContent: "space-around"
  },
  tabButton: {
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 999,
    backgroundColor: "rgba(255,255,255,0.1)"
  },
  tabButtonActive: {
    backgroundColor: "#00d1ff"
  },
  tabButtonText: {
    color: "rgba(255,255,255,0.75)",
    fontWeight: "600"
  },
  tabButtonTextActive: {
    color: "#001021"
  },
  highlightList: {
    gap: 12
  },
  highlightCard: {
    backgroundColor: "rgba(255,255,255,0.1)",
    borderRadius: 20,
    overflow: "hidden",
    flexDirection: "row"
  },
  highlightPreview: {
    width: 110,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#00d1ff"
  },
  highlightBadge: {
    color: "#001021",
    fontWeight: "700"
  },
  highlightDetails: {
    flex: 1,
    padding: 12,
    justifyContent: "space-between"
  },
  highlightTitle: {
    color: "#ffffff",
    fontSize: 18,
    fontWeight: "700"
  },
  highlightSubtitle: {
    color: "rgba(255,255,255,0.7)"
  },
  shareButton: {
    alignSelf: "flex-start",
    backgroundColor: "#00d1ff",
    borderRadius: 12,
    paddingVertical: 6,
    paddingHorizontal: 12
  },
  shareButtonText: {
    color: "#001021",
    fontWeight: "700"
  },
  leaderboardContainer: {
    gap: 16
  },
  leaderboardCard: {
    backgroundColor: "rgba(255,255,255,0.1)",
    borderRadius: 20,
    padding: 16
  },
  leaderboardTitle: {
    color: "#ffffff",
    fontSize: 18,
    fontWeight: "700",
    marginBottom: 12
  },
  leaderboardRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 12
  },
  leaderboardRank: {
    width: 24,
    color: "#00d1ff",
    fontWeight: "700"
  },
  leaderboardInfo: {
    flex: 1
  },
  leaderboardPlayer: {
    color: "#ffffff",
    fontWeight: "600"
  },
  leaderboardRegion: {
    color: "rgba(255,255,255,0.6)",
    fontSize: 12
  },
  leaderboardScore: {
    color: "#ffffff",
    fontWeight: "700"
  }
});
