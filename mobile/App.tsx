import React, { useCallback, useMemo, useState } from "react";
import {
  SafeAreaView,
  View,
  Text,
  TouchableOpacity,
  FlatList,
  StyleSheet,
  Share,
} from "react-native";

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
  { id: "hits", label: "Most Hits" },
];

const highlightData: Highlight[] = [
  {
    id: "1",
    title: "Crossbar Laser",
    subtitle: "112 km/h . Left Foot",
    badge: "TOP BINS",
    assetPath: "file:///highlights/highlight-1.mp4",
    speed: 112,
  },
  {
    id: "2",
    title: "Volley Rocket",
    subtitle: "108 km/h . Right Foot",
    badge: "PERSONAL BEST",
    assetPath: "file:///highlights/highlight-2.mp4",
    speed: 108,
  },
];

const hardestShot: LeaderboardEntry[] = [
  { id: "h1", player: "J. Alvarez", score: "118 km/h", region: "Global" },
  { id: "h2", player: "S. Ito", score: "115 km/h", region: "Tokyo" },
  { id: "h3", player: "M. Smith", score: "113 km/h", region: "Austin" },
];

const mostHits: LeaderboardEntry[] = [
  { id: "m1", player: "J. Alvarez", score: "17 hits", region: "Global" },
  { id: "m2", player: "A. Lopes", score: "16 hits", region: "Lisbon" },
  { id: "m3", player: "K. Singh", score: "15 hits", region: "Delhi" },
];

function useShareHandler() {
  return useCallback(async (highlight: Highlight) => {
    await Share.share({
      title: highlight.title,
      message: `${highlight.title} — ${highlight.speed} km/h`,
      url: highlight.assetPath,
    });
  }, []);
}

const TabButton: React.FC<{ id: string; label: string; active: boolean; onPress: (id: string) => void }> = ({
  id,
  label,
  active,
  onPress,
 }) => {
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
  onShare,
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

const App: React.FC = () => {
  const [tab, setTab] = useState<string>("highlights");
  const onShare = useShareHandler();

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
      <Text style={styles.header}>Highlights & Leaderboards</Text>
      <View style={styles.tabBar}>
        {TABS.map((tabItem) => (
          <TabButton key={tabItem.id} {...tabItem} active={tabItem.id === tab} onPress={setTab} />
        ))}
      </View>
      {tab === "highlights" ? (
        <FlatList
          contentContainerStyle={styles.highlightList}
          data={highlightData}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => <HighlightCard highlight={item} onShare={onShare} />}
        />
      ) : (
        <View style={styles.leaderboardContainer}>{leaderboardContent}</View>
      )}
    </SafeAreaView>
  );
};

export default App;

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0c1524",
    paddingHorizontal: 16,
  },
  header: {
    fontSize: 24,
    fontWeight: "700",
    color: "#ffffff",
    marginVertical: 16,
  },
  tabBar: {
    flexDirection: "row",
    justifyContent: "space-around",
    marginBottom: 12,
  },
  tabButton: {
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 999,
    backgroundColor: "rgba(255,255,255,0.1)",
  },
  tabButtonActive: {
    backgroundColor: "#00d1ff",
  },
  tabButtonText: {
    color: "rgba(255,255,255,0.75)",
    fontWeight: "600",
  },
  tabButtonTextActive: {
    color: "#001021",
  },
  highlightList: {
    paddingBottom: 24,
    gap: 12,
  },
  highlightCard: {
    backgroundColor: "rgba(255,255,255,0.1)",
    borderRadius: 20,
    overflow: "hidden",
    flexDirection: "row",
  },
  highlightPreview: {
    width: 110,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#00d1ff",
  },
  highlightBadge: {
    color: "#001021",
    fontWeight: "700",
  },
  highlightDetails: {
    flex: 1,
    padding: 12,
    justifyContent: "space-between",
  },
  highlightTitle: {
    color: "#ffffff",
    fontSize: 18,
    fontWeight: "700",
  },
  highlightSubtitle: {
    color: "rgba(255,255,255,0.7)",
  },
  shareButton: {
    alignSelf: "flex-start",
    backgroundColor: "#00d1ff",
    borderRadius: 12,
    paddingVertical: 6,
    paddingHorizontal: 12,
  },
  shareButtonText: {
    color: "#001021",
    fontWeight: "700",
  },
  leaderboardContainer: {
    flex: 1,
    gap: 16,
  },
  leaderboardCard: {
    backgroundColor: "rgba(255,255,255,0.1)",
    borderRadius: 20,
    padding: 16,
  },
  leaderboardTitle: {
    color: "#ffffff",
    fontSize: 18,
    fontWeight: "700",
    marginBottom: 12,
  },
  leaderboardRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 12,
  },
  leaderboardRank: {
    width: 24,
    color: "#00d1ff",
    fontWeight: "700",
  },
  leaderboardInfo: {
    flex: 1,
  },
  leaderboardPlayer: {
    color: "#ffffff",
    fontWeight: "600",
  },
  leaderboardRegion: {
    color: "rgba(255,255,255,0.6)",
    fontSize: 12,
  },
  leaderboardScore: {
    color: "#ffffff",
    fontWeight: "700",
  },
});
