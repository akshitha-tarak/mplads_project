import Papa from 'papaparse';

const csvToJson = async (url: string) => {
  const res = await fetch(url);
  const text = await res.text();
  return Papa.parse(text, { header: true, skipEmptyLines: true }).data as any[];
};

const normalizeProjectId = (value: unknown): string => {
  const text = String(value ?? '').trim();
  if (!text) return '';
  const match = text.match(/WS\/?\s*MP\d+\/\d{4}-\d{4}\/\d+/i);
  if (match) {
    return match[0].replace(/\s+/g, '');
  }
  return text;
};

const toNumber = (value: unknown) => {
  const raw = String(value ?? '').replace(/[^0-9.-]/g, '');
  if (!raw) return 0;
  const num = Number(raw);
  return Number.isFinite(num) ? num : 0;
};

const pickValue = (...values: unknown[]) => {
  for (const value of values) {
    if (value !== null && value !== undefined && String(value).trim() !== '') {
      return value;
    }
  }
  return '';
};

export const toBooleanFlag = (value: unknown): boolean => {
  if (value === null || value === undefined) return false;

  if (typeof value === 'boolean') return value;

  const raw = String(value).trim();
  if (!raw) return false;

  const lower = raw.toLowerCase();
  if (['true', 'yes', 'y', 't'].includes(lower)) return true;
  if (['false', 'no', 'n', 'f'].includes(lower)) return false;

  const numeric = Number(raw);
  if (!Number.isNaN(numeric)) return numeric !== 0;

  return false;
};

export const getMlOutputs = async () => {
  return csvToJson('/data/processed/m2_ml_outputs.csv');
};

export const getCostAnomalies = async () => {
  return csvToJson('/data/processed/cost_anomaly_outputs.csv');
};

export const getDuplicates = async () => {
  return csvToJson('/data/processed/duplicate_outputs.csv');
};

export const getProjects = async () => {
  const [recommended, sanctioned, completed, expenditure, mlRows, duplicateRows, anomalyRows] = await Promise.all([
    csvToJson('/data/dataset/Works Recommended.csv').catch(() => []),
    csvToJson('/data/dataset/Works Sanctioned.csv').catch(() => []),
    csvToJson('/data/dataset/Works Completed.csv').catch(() => []),
    csvToJson('/data/dataset/Expenditure on Completed and On-going Works as on Date.csv').catch(() => []),
    csvToJson('/data/processed/m2_ml_outputs.csv').catch(() => []),
    csvToJson('/data/processed/duplicate_outputs.csv').catch(() => []),
    csvToJson('/data/processed/cost_anomaly_outputs.csv').catch(() => []),
  ]);

  const recMap = new Map<string, any>();
  const sancMap = new Map<string, any>();
  const compMap = new Map<string, any>();
  const expMap = new Map<string, number>();
  const mlMap = new Map<string, any>();
  const duplicateMap = new Map<string, any>();
  const anomalyMap = new Map<string, any>();

  for (const row of recommended) {
    const id = normalizeProjectId(pickValue(row['Work'], row['WORK'], row.project_id, row['Work ID']));
    if (id) recMap.set(id, row);
  }

  for (const row of sanctioned) {
    const id = normalizeProjectId(pickValue(row['Work'], row['WORK'], row.project_id, row['Work ID']));
    if (id) sancMap.set(id, row);
  }

  for (const row of completed) {
    const id = normalizeProjectId(pickValue(row['Work'], row['WORK'], row.project_id, row['Work ID']));
    if (id) compMap.set(id, row);
  }

  for (const row of expenditure) {
    const id = normalizeProjectId(pickValue(row['Work ID'], row['Work'], row['WORK'], row.project_id));
    if (!id) continue;
    const amount = toNumber(row['Fund Disbursed Amount ( ₹ )'] ?? row['Fund Disbursed Amount']);
    expMap.set(id, (expMap.get(id) ?? 0) + amount);
  }

  for (const row of mlRows) {
    const id = normalizeProjectId(row.project_id ?? row['project_id']);
    if (id) mlMap.set(id, row);
  }

  for (const row of duplicateRows) {
    const id = normalizeProjectId(row.project_id ?? row['project_id']);
    if (id) duplicateMap.set(id, row);
  }

  for (const row of anomalyRows) {
    const id = normalizeProjectId(row.project_id ?? row['project_id']);
    if (id) anomalyMap.set(id, row);
  }

  const ids = new Set<string>([
    ...Array.from(recMap.keys()),
    ...Array.from(sancMap.keys()),
    ...Array.from(compMap.keys()),
    ...Array.from(expMap.keys()),
    ...Array.from(mlMap.keys()),
    ...Array.from(duplicateMap.keys()),
    ...Array.from(anomalyMap.keys()),
  ]);

  return Array.from(ids)
    .filter(Boolean)
    .map((id) => {
      const recommendedRow = recMap.get(id) ?? {};
      const sanctionedRow = sancMap.get(id) ?? {};
      const completedRow = compMap.get(id) ?? {};
      const mlRow = mlMap.get(id) ?? {};
      const duplicateRow = duplicateMap.get(id) ?? {};
      const anomalyRow = anomalyMap.get(id) ?? {};

      return {
        project_id: id,
        'Work category': pickValue(sanctionedRow['Work category'], recommendedRow['Work category'], completedRow['Work Category'], recommendedRow['Work Category']),
        Work: pickValue(sanctionedRow['Work'], recommendedRow['WORK'], recommendedRow['Work'], completedRow['Work'], mlRow.project_id),
        State: pickValue(sanctionedRow['State'], recommendedRow['State'], completedRow['State']),
        IDA: pickValue(sanctionedRow['IDA'], recommendedRow['IDA'], completedRow['IDA']),
        "Hon'ble Members of Parliament": pickValue(sanctionedRow["Hon'ble Members of Parliament"], recommendedRow["Hon'ble Members of Parliament"], completedRow["Hon'ble Members of Parliament"]),
        Constituency: pickValue(sanctionedRow['Constituency'], recommendedRow['Constituency'], completedRow['Constituency']),
        'Work description': pickValue(sanctionedRow['Work description'], recommendedRow['Work description'], completedRow['Work Description']),
        'Recommended date': pickValue(recommendedRow['Recommended date'], sanctionedRow['Recommended date']),
        'Sanction Date': pickValue(sanctionedRow['Sanction Date'], recommendedRow['Sanction Date']),
        'Sanction Amount ( ₹ )': toNumber(pickValue(sanctionedRow['Sanction Amount ( ₹ )'], recommendedRow['RECOMMENDED AMOUNT   ( ₹ )'], recommendedRow['Recommended Amount ( ₹ )'])),
        'Recommended Amount ( ₹ )': toNumber(pickValue(recommendedRow['RECOMMENDED AMOUNT   ( ₹ )'], recommendedRow['Recommended Amount ( ₹ )'])),
        'Work Status': pickValue(sanctionedRow['Work Status']),
        'Completion Date': pickValue(completedRow['Completion Date']),
        'Amount Disbursed ( ₹ )': toNumber(pickValue(completedRow['Amount Disbursed ( ₹ )'])),
        'Fund Disbursed Amount ( ₹ )': expMap.get(id) ?? 0,
        exact_duplicate_flag: duplicateRow.exact_duplicate_flag ?? '',
        potential_duplicate_flag: duplicateRow.potential_duplicate_flag ?? '',
        duplicate_reason: duplicateRow.duplicate_reason ?? '',
        similar_project_id: duplicateRow.similar_project_id ?? '',
        cost_anomaly_flag: anomalyRow.cost_anomaly_flag ?? mlRow.cost_anomaly_flag ?? '',
        cost_anomaly_score: anomalyRow.cost_anomaly_score ?? mlRow.cost_anomaly_score ?? '',
        cost_anomaly_reason: anomalyRow.cost_anomaly_reason ?? mlRow.cost_anomaly_reason ?? '',
        cost_anomaly_available: anomalyRow.cost_anomaly_available ?? mlRow.cost_anomaly_available ?? '',
      };
    })
    .sort((a, b) => a.project_id.localeCompare(b.project_id));
};

export const getMasterProjects = async () => getProjects();

export default {
  getMlOutputs,
  getCostAnomalies,
  getDuplicates,
  getProjects,
  getMasterProjects,
};