export function generateLicenseKey(isTestMode = false): string {
  const prefix = isTestMode ? "sch_test_" : "sch_live_";
  const bytes = new Uint8Array(32);
  crypto.getRandomValues(bytes);
  const hex = Array.from(bytes)
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
  return `${prefix}${hex}`;
}

export async function hashLicenseKey(licenseKey: string, pepper: string): Promise<string> {
  const cleanKey = license_key_clean(licenseKey);
  const payload = `${cleanKey}::${pepper}`;
  const encoder = new TextEncoder();
  const data = encoder.encode(payload);
  const hashBuffer = await crypto.subtle.digest("SHA-256", data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");
}

export function getKeyPrefix(licenseKey: string): string {
  const cleanKey = license_key_clean(licenseKey);
  return cleanKey.slice(0, 16);
}

export async function hashDeviceFingerprint(deviceId: string): Promise<string> {
  const cleanId = deviceId.trim();
  const encoder = new TextEncoder();
  const data = encoder.encode(`device::${cleanId}`);
  const hashBuffer = await crypto.subtle.digest("SHA-256", data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");
}

function license_key_clean(key: string): string {
  return key.trim();
}
