import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  SafeAreaView,
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  Share,
  TextInput,
  Platform,
  AppState,
  AppStateStatus,
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

type Tier = "free" | "pro" | "elite";

type EntitlementSnapshot = {
  userId: string;
  tier: Tier;
  provider: string | null;
  expiresAt: string | null;
  entitlements: { free: boolean; pro: boolean; elite: boolean };
  features: Record<string, boolean>;
};

const FEATURE_KEYS = {
  AI_PERSONAS: "AI_PERSONAS",
  ADVANCED_METRICS: "ADVANCED_METRICS",
  TEAM_DASHBOARD: "TEAM_DASHBOARD",
} as const;

function normaliseSnapshot(payload: Partial<EntitlementSnapshot> | null | undefined): EntitlementSnapshot {
  const tier = (payload?.tier ?? "free") as Tier;
  const entitlements = payload?.entitlements ?? {};
  const features = payload?.features ?? {};
  const pro = entitlements.pro ?? tier === "pro" || tier === "elite";
  const elite = entitlements.elite ?? tier === "elite";
  return {
    userId: payload?.userId ?? USER_ID,
    tier,
    provider: payload?.provider ?? null,
    expiresAt: payload?.expiresAt ?? null,
    entitlements: {
      free: true,
      pro,
      elite,
    },
    features: {
      [FEATURE_KEYS.AI_PERSONAS]: Boolean(features[FEATURE_KEYS.AI_PERSONAS] ?? pro),
      [FEATURE_KEYS.ADVANCED_METRICS]: Boolean(features[FEATURE_KEYS.ADVANCED_METRICS] ?? pro),
      [FEATURE_KEYS.TEAM_DASHBOARD]: Boolean(features[FEATURE_KEYS.TEAM_DASHBOARD] ?? elite),
    },
  };
}

const API_BASE = (globalThis as any).API_BASE ?? "";
const USER_ID = (globalThis as any).CURRENT_USER_ID ?? "mock-user";

const TABS = [
  { id: "highlights", label: "Highlights" },
  { id: "hardest", label: "Hardest Shot" },
  { id: "hits", label: "Most Hits" },
];

const personaCatalog = [
  {
    id: "visionary",
    name: "Visionary Playmaker",
    tagline: "Elite build-up schemes generated for every possession.",
  },
  {
    id: "finisher",
    name: "Clinical Finisher",
    tagline: "Progressive finishing ladders tuned to first touch and stance.",
  },
  {
    id: "guardian",
    name: "Backline Guardian",
    tagline: "Shape and pressure cues for locking down the defensive third.",
  },
];

const highlightData: Highlight[] = [
  {
    id: "1",
    title: "Crossbar Laser",
    subtitle: "112 km/h · Left Foot",
    badge: "TOP BINS",
    assetPath: "file:///highlights/highlight-1.mp4",
    speed: 112,
  },
  {
    id: "2",
    title: "Volley Rocket",
    subtitle: "108 km/h · Right Foot",
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

type TabButtonProps = {
  id: string;
  label: string;
  active: boolean;
  onPress: (id: string) => void;
};

const TabButton: React.FC<TabButtonProps> = ({ id, label, active, onPress }) => {
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

type HighlightCardProps = {
  highlight: Highlight;
  onShare: (highlight: Highlight) => void;
};

const HighlightCard: React.FC<HighlightCardProps> = ({ highlight, onShare }) => (
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

type LeaderboardListProps = {
  title: string;
  data: LeaderboardEntry[];
};

const LeaderboardList: React.FC<LeaderboardListProps> = ({ title, data }) => (
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

type BillingBannerProps = {
  loading: boolean;
  error: string | null;
  tier: EntitlementSnapshot["tier"];
};

const BillingBanner: React.FC<BillingBannerProps> = ({ loading, error, tier }) => {
  const bannerStyles = [styles.billingBanner];
  let message = `Current tier: ${tier.toUpperCase()}`;
  if (loading) {
    message = "Checking subscription…";
    bannerStyles.push(styles.billingBannerPending);
  }
  if (error) {
    message = error;
    bannerStyles.push(styles.billingBannerError);
  }
  return (
    <View style={bannerStyles}>
      <Text style={styles.billingBannerText}>{message}</Text>
    </View>
  );
};

type UpgradeCTAProps = {
  copy: string;
  onPress: () => void;
};

const UpgradeCTA: React.FC<UpgradeCTAProps> = ({ copy, onPress }) => (
  <TouchableOpacity style={styles.upgradeCta} onPress={onPress} activeOpacity={0.9}>
    <Text style={styles.upgradeCtaCopy}>{copy}</Text>
    <View style={styles.upgradeCtaButton}>
      <Text style={styles.upgradeCtaButtonText}>Upgrade</Text>
    </View>
  </TouchableOpacity>
);

type PersonaCardProps = {
  name: string;
  tagline: string;
  locked: boolean;
};

const PersonaCard: React.FC<PersonaCardProps> = ({ name, tagline, locked }) => (
  <View style={[styles.personaCard, locked && styles.personaCardLocked]}>
    <Text style={styles.personaName}>{name}</Text>
    <Text style={styles.personaTagline}>{tagline}</Text>
    <Text style={[styles.personaPill, locked && styles.personaPillLocked]}>
      {locked ? "Locked" : "Included"}
    </Text>
  </View>
);

type UpgradeScreenProps = {
  receipt: string;
  onChangeReceipt: (text: string) => void;
  onSubmit: () => void;
  submitting: boolean;
  message: string;
  error: string;
  currentTier: EntitlementSnapshot["tier"];
  onRestore: () => void;
  restoring: boolean;
  onClose: () => void;
};

const UpgradeScreen: React.FC<UpgradeScreenProps> = ({
  receipt,
  onChangeReceipt,
  onSubmit,
  submitting,
  message,
  error,
  currentTier,
  onRestore,
  restoring,
  onClose,
}) => {
  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.upgradeContainer}>
        <Text style={styles.header}>Activate SoccerIQ Pro</Text>
        <Text style={styles.upgradeCopy}>
          Use mock receipts (PRO-* or ELITE-*) to simulate App Store and Play Store upgrades while checkout is under review.
        </Text>
        <Text style={styles.upgradeStatus}>Current tier: {currentTier.toUpperCase()}</Text>
        <TextInput
          accessibilityLabel="Receipt code"
          style={styles.input}
          placeholder="PRO-123"
          autoCapitalize="characters"
          autoCorrect={false}
          value={receipt}
          onChangeText={onChangeReceipt}
        />
        {error ? <Text style={styles.errorText}>{error}</Text> : null}
        {message ? <Text style={styles.successText}>{message}</Text> : null}
        <TouchableOpacity
          style={[styles.actionButton, submitting && styles.actionButtonDisabled]}
          onPress={onSubmit}
          disabled={submitting}
        >
          <Text style={styles.actionButtonText}>{submitting ? "Activating…" : "Activate"}</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.restoreButton, (submitting || restoring) && styles.restoreButtonDisabled]}
          onPress={onRestore}
          disabled={submitting || restoring}
        >
          <Text style={styles.restoreButtonText}>{restoring ? "Restoring…" : "Restore purchases"}</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.backButton} onPress={onClose}>
          <Text style={styles.backButtonText}>Back to home</Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
};

const App: React.FC = () => {
  const [tab, setTab] = useState<string>("highlights");
  const [screen, setScreen] = useState<"home" | "upgrade">("home");
  const [entitlements, setEntitlements] = useState<EntitlementSnapshot>(normaliseSnapshot(null));
  const [accessLoading, setAccessLoading] = useState<boolean>(true);
  const [accessError, setAccessError] = useState<string | null>(null);
  const [receipt, setReceipt] = useState<string>("");
  const [upgradeSubmitting, setUpgradeSubmitting] = useState<boolean>(false);
  const [restorePending, setRestorePending] = useState<boolean>(false);
  const [upgradeMessage, setUpgradeMessage] = useState<string>("");
  const [upgradeError, setUpgradeError] = useState<string>("");
  const onShare = useShareHandler();
  const lastUpgradeViewAt = useRef<number>(0);
  const provider = Platform.OS === "ios" ? "app_store" : "google_play";

  const emitTelemetry = useCallback(async (event: string, props: Record<string, unknown> = {}) => {
    try {
      await fetch(`${API_BASE}/ws/telemetry`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          event,
          userId: USER_ID,
          platform: Platform.OS,
          timestampMs: Date.now(),
          ...props,
        }),
      });
    } catch (error) {
      console.warn("telemetry failed", error);
    }
  }, []);

  const refreshEntitlements = useCallback(async () => {
    setAccessLoading(true);
    setAccessError(null);
    try {
      const response = await fetch(
        `${API_BASE}/me/entitlements?userId=${encodeURIComponent(USER_ID)}`,
      );
      if (!response.ok) {
        throw new Error(`status ${response.status}`);
      }
      const data = (await response.json()) as Partial<EntitlementSnapshot>;
      setEntitlements(normaliseSnapshot(data));
    } catch (err) {
      console.error("Failed to fetch entitlements", err);
      setAccessError("Unable to refresh entitlements.");
    } finally {
      setAccessLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshEntitlements();
    const handleAppStateChange = (next: AppStateStatus) => {
      if (next === "active") {
        refreshEntitlements();
      }
    };
    const subscription = AppState.addEventListener("change", handleAppStateChange);
    return () => {
      subscription.remove();
    };
  }, [refreshEntitlements]);

  const isPro = entitlements.entitlements.pro;

  const personaList = useMemo(() => {
    const unlockedCount = entitlements.features[FEATURE_KEYS.AI_PERSONAS]
      ? personaCatalog.length
      : 1;
    return personaCatalog.map((persona, index) => ({
      ...persona,
      locked: index >= unlockedCount,
    }));
  }, [entitlements.features]);

  const handleUpgrade = useCallback(async () => {
    const trimmed = receipt.trim();
    if (!trimmed) {
      setUpgradeError("Enter a mock receipt (PRO-* or ELITE-*).");
      setUpgradeMessage("");
      return;
    }
    setUpgradeSubmitting(true);
    setUpgradeError("");
    setUpgradeMessage("");
    try {
      emitTelemetry("start_checkout", { provider });
      const response = await fetch(`${API_BASE}/billing/receipt`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          userId: USER_ID,
          platform: Platform.OS === "ios" ? "ios" : "android",
          receipt: trimmed,
        }),
      });
      if (!response.ok) {
        throw new Error(`status ${response.status}`);
      }
      const data = (await response.json()) as Partial<EntitlementSnapshot>;
      setUpgradeMessage(`Activated ${(data.tier ?? "pro").toUpperCase()}.`);
      setReceipt("");
      setEntitlements(normaliseSnapshot(data));
      setAccessError(null);
      emitTelemetry("receipt_verified", { provider, tier: data.tier ?? "pro" });
      await refreshEntitlements();
      setScreen("home");
    } catch (err) {
      console.error("Failed to verify receipt", err);
      setUpgradeError("Verification failed. Check the receipt and try again.");
    } finally {
      setUpgradeSubmitting(false);
    }
  }, [provider, receipt, refreshEntitlements, emitTelemetry]);

  const handleRestore = useCallback(async () => {
    setRestorePending(true);
    setUpgradeError("");
    setUpgradeMessage("");
    emitTelemetry("restore_clicked", { provider });
    try {
      const response = await fetch(`${API_BASE}/billing/receipt`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          userId: USER_ID,
          platform: Platform.OS === "ios" ? "ios" : "android",
          mode: "restore",
        }),
      });
      if (!response.ok) {
        throw new Error(`status ${response.status}`);
      }
      const data = (await response.json()) as Partial<EntitlementSnapshot>;
      setEntitlements(normaliseSnapshot(data));
      setAccessError(null);
      setUpgradeMessage("Restored your subscription.");
      await refreshEntitlements();
      setScreen("home");
    } catch (err) {
      console.error("Failed to restore purchases", err);
      setUpgradeError("Restore failed. Try again shortly.");
    } finally {
      setRestorePending(false);
    }
  }, [provider, refreshEntitlements, emitTelemetry]);

  useEffect(() => {
    if (screen === "upgrade") {
      const now = Date.now();
      if (now - lastUpgradeViewAt.current > 500) {
        lastUpgradeViewAt.current = now;
        emitTelemetry("view_upgrade", { source: "mobile" });
      }
    }
  }, [screen, emitTelemetry]);

  const showUpgradeFor = useCallback(
    (featureId: string) => {
      emitTelemetry("feature_blocked", { feature: featureId, source: "mobile" });
      setScreen("upgrade");
    },
    [emitTelemetry],
  );

  const leaderboardContent = useMemo(() => {
    if (tab === "hardest") {
      return <LeaderboardList title="Hardest Shot — 7 Days" data={hardestShot} />;
    }
    if (tab === "hits") {
      return <LeaderboardList title="Most Hits — 7 Days" data={mostHits} />;
    }
    return null;
  }, [tab]);

  if (screen === "upgrade") {
    return (
      <UpgradeScreen
        receipt={receipt}
        onChangeReceipt={setReceipt}
        onSubmit={handleUpgrade}
        submitting={upgradeSubmitting}
        message={upgradeMessage}
        error={upgradeError}
        currentTier={entitlements.tier}
        onRestore={handleRestore}
        restoring={restorePending}
        onClose={() => setScreen("home")}
      />
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <Text style={styles.header}>Highlights & Leaderboards</Text>
        <BillingBanner loading={accessLoading} error={accessError} tier={entitlements.tier} />

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Coach Personas</Text>
          <Text style={styles.sectionCopy}>
            Personalized training blueprints voiced by expert coaches for your squad.
          </Text>
          <View style={styles.personaGrid}>
            {personaList.map((persona) => (
              <PersonaCard
                key={persona.id}
                name={persona.name}
                tagline={persona.tagline}
                locked={persona.locked}
              />
            ))}
          </View>
          {!isPro ? (
            <UpgradeCTA copy="Unlock all coach personas" onPress={() => showUpgradeFor("coach_personas")} />
          ) : null}
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>AR Target Precision</Text>
          <Text style={styles.sectionCopy}>
            Overlay augmented targets on your net and log finishing accuracy streaks automatically.
          </Text>
          {isPro ? (
            <View style={styles.unlockedCard}>
              <Text style={styles.unlockedText}>
                ✅ Precision tracking unlocked. Calibrate your target to start scoring every drill.
              </Text>
            </View>
          ) : (
            <UpgradeCTA copy="Unlock AR Target precision scoring" onPress={() => showUpgradeFor("ar_precision")} />
          )}
        </View>

        <View style={styles.tabBar}>
          {TABS.map((tabItem) => (
            <TabButton key={tabItem.id} {...tabItem} active={tabItem.id === tab} onPress={setTab} />
          ))}
        </View>

        {tab === "highlights" ? (
          <View style={styles.highlightList}>
            {highlightData.map((item) => (
              <HighlightCard key={item.id} highlight={item} onShare={onShare} />
            ))}
          </View>
        ) : (
          <View style={styles.leaderboardContainer}>{leaderboardContent}</View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
};

export default App;

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0c1524",
  },
  scrollContent: {
    paddingHorizontal: 16,
    paddingBottom: 32,
  },
  header: {
    fontSize: 24,
    fontWeight: "700",
    color: "#ffffff",
    marginVertical: 16,
  },
  billingBanner: {
    borderRadius: 12,
    padding: 12,
    backgroundColor: "rgba(16, 185, 129, 0.15)",
    borderWidth: 1,
    borderColor: "rgba(16, 185, 129, 0.3)",
    marginBottom: 16,
  },
  billingBannerPending: {
    backgroundColor: "rgba(255, 159, 67, 0.15)",
    borderColor: "rgba(255, 159, 67, 0.4)",
  },
  billingBannerError: {
    backgroundColor: "rgba(250, 82, 82, 0.15)",
    borderColor: "rgba(250, 82, 82, 0.4)",
  },
  billingBannerText: {
    color: "#e0fff4",
    fontWeight: "600",
  },
  section: {
    backgroundColor: "rgba(16, 24, 40, 0.85)",
    borderRadius: 20,
    padding: 16,
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: "#ffffff",
    marginBottom: 8,
  },
  sectionCopy: {
    color: "rgba(226, 232, 240, 0.75)",
    marginBottom: 16,
  },
  personaGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "space-between",
  },
  personaCard: {
    backgroundColor: "rgba(15, 23, 42, 0.9)",
    borderRadius: 16,
    padding: 12,
    width: "48%",
    marginBottom: 12,
  },
  personaCardLocked: {
    opacity: 0.5,
  },
  personaName: {
    color: "#e2e8f0",
    fontWeight: "700",
    marginBottom: 6,
  },
  personaTagline: {
    color: "rgba(226, 232, 240, 0.75)",
    marginBottom: 8,
    fontSize: 12,
  },
  personaPill: {
    alignSelf: "flex-start",
    backgroundColor: "rgba(16, 185, 129, 0.15)",
    color: "#2dd4bf",
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 999,
    fontSize: 12,
    fontWeight: "700",
  },
  personaPillLocked: {
    backgroundColor: "rgba(239, 68, 68, 0.15)",
    color: "#f87171",
  },
  unlockedCard: {
    backgroundColor: "rgba(45, 212, 191, 0.15)",
    borderRadius: 14,
    padding: 12,
  },
  unlockedText: {
    color: "#2dd4bf",
    fontWeight: "600",
  },
  upgradeCta: {
    backgroundColor: "rgba(255, 159, 67, 0.15)",
    borderRadius: 16,
    padding: 16,
    marginTop: 12,
  },
  upgradeCtaCopy: {
    color: "#ffdd99",
    marginBottom: 12,
    fontWeight: "600",
  },
  upgradeCtaButton: {
    alignSelf: "flex-start",
    backgroundColor: "#ff922b",
    borderRadius: 999,
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  upgradeCtaButtonText: {
    color: "#001021",
    fontWeight: "700",
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
    width: "100%",
  },
  highlightCard: {
    backgroundColor: "rgba(15, 23, 42, 0.9)",
    borderRadius: 20,
    overflow: "hidden",
    flexDirection: "row",
    marginBottom: 16,
  },
  highlightPreview: {
    width: 100,
    backgroundColor: "#00d1ff",
    alignItems: "center",
    justifyContent: "center",
  },
  highlightBadge: {
    color: "#001021",
    fontWeight: "700",
  },
  highlightDetails: {
    flex: 1,
    padding: 16,
  },
  highlightTitle: {
    color: "#ffffff",
    fontWeight: "700",
    fontSize: 16,
  },
  highlightSubtitle: {
    color: "rgba(226, 232, 240, 0.75)",
    marginBottom: 8,
  },
  shareButton: {
    alignSelf: "flex-start",
    backgroundColor: "#00d1ff",
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  shareButtonText: {
    color: "#001021",
    fontWeight: "700",
  },
  leaderboardContainer: {
    width: "100%",
  },
  leaderboardCard: {
    backgroundColor: "rgba(15, 23, 42, 0.9)",
    borderRadius: 20,
    padding: 16,
    marginBottom: 16,
  },
  leaderboardTitle: {
    color: "#ffffff",
    fontWeight: "700",
    marginBottom: 12,
  },
  leaderboardRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 8,
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
    color: "rgba(226, 232, 240, 0.6)",
    fontSize: 12,
  },
  leaderboardScore: {
    color: "#00d1ff",
    fontWeight: "600",
  },
  upgradeContainer: {
    paddingHorizontal: 20,
    paddingBottom: 40,
  },
  upgradeCopy: {
    color: "rgba(226, 232, 240, 0.75)",
    marginBottom: 12,
  },
  upgradeStatus: {
    color: "#ffffff",
    fontWeight: "600",
    marginBottom: 16,
  },
  input: {
    backgroundColor: "#ffffff",
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 16,
    marginBottom: 12,
  },
  actionButton: {
    backgroundColor: "#00d1ff",
    borderRadius: 999,
    paddingVertical: 12,
    alignItems: "center",
    marginTop: 4,
  },
  actionButtonDisabled: {
    opacity: 0.6,
  },
  actionButtonText: {
    color: "#001021",
    fontWeight: "700",
    fontSize: 16,
  },
  restoreButton: {
    marginTop: 16,
    alignSelf: "center",
  },
  restoreButtonDisabled: {
    opacity: 0.6,
  },
  restoreButtonText: {
    color: "#fbbf24",
    fontWeight: "600",
  },
  errorText: {
    color: "#f87171",
    marginBottom: 8,
    fontWeight: "600",
  },
  successText: {
    color: "#34d399",
    marginBottom: 8,
    fontWeight: "600",
  },
  backButton: {
    marginTop: 20,
    alignSelf: "center",
  },
  backButtonText: {
    color: "#00d1ff",
    fontWeight: "600",
  },
});
