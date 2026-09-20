import { useMemo, useState } from "react";
import "./App.css";

type Status = "HEALTHY" | "AT RISK" | "CRITICAL";

type Machine = {
  id: string;
  name: string;
  process: string;
  health: number;
  failure: number;
  anomaly: number;
  anomalyRatio?: number;
  rul: number;
  temperature: number;
  vibration: number;
  toolWear: number;
  rpm: number;
  torque: number;
  status: Status;
};

type SensorForm = {
  machineId: string;
  component: string;
  operation: string;

  airTemperature: string;
  processTemperature: string;

  rpm: string;
  current: string;
  torque: string;

  vibrationX: string;
  vibrationY: string;
  vibrationZ: string;

  pressure: string;
  cuttingForce: string;
  acousticEmission: string;

  toolWear: string;
  toolAge: string;
};

const API_URL = "https://fortress-production-9b47.up.railway.app";

const initialMachines: Machine[] = [
  {
    id: "CNC-001",
    name: "Engine Block Cell",
    process: "Precision Milling",
    health: 91,
    failure: 8,
    anomaly: 11,
    rul: 286,
    temperature: 64.2,
    vibration: 2.1,
    toolWear: 18,
    rpm: 4520,
    torque: 41.2,
    status: "HEALTHY",
  },
  {
    id: "CNC-002",
    name: "Cylinder Head Cell",
    process: "High-Speed Boring",
    health: 76,
    failure: 24,
    anomaly: 29,
    rul: 174,
    temperature: 71.5,
    vibration: 3.8,
    toolWear: 43,
    rpm: 4380,
    torque: 49.6,
    status: "AT RISK",
  },
  {
    id: "CNC-003",
    name: "Transmission Housing",
    process: "CNC Turning",
    health: 58,
    failure: 48,
    anomaly: 54,
    rul: 92,
    temperature: 78.4,
    vibration: 5.4,
    toolWear: 67,
    rpm: 4210,
    torque: 55.1,
    status: "AT RISK",
  },
  {
    id: "CNC-004",
    name: "Crankshaft Cell",
    process: "Precision Turning",
    health: 39,
    failure: 71,
    anomaly: 68,
    rul: 61,
    temperature: 84.7,
    vibration: 7.2,
    toolWear: 81,
    rpm: 4060,
    torque: 61.8,
    status: "CRITICAL",
  },
  {
    id: "CNC-005",
    name: "Gear Machining Cell",
    process: "Gear Hobbing",
    health: 87,
    failure: 13,
    anomaly: 15,
    rul: 231,
    temperature: 67.3,
    vibration: 2.7,
    toolWear: 25,
    rpm: 4610,
    torque: 43.4,
    status: "HEALTHY",
  },
  {
    id: "CNC-006",
    name: "Camshaft Cell",
    process: "CNC Grinding",
    health: 68,
    failure: 32,
    anomaly: 37,
    rul: 137,
    temperature: 74.1,
    vibration: 4.6,
    toolWear: 51,
    rpm: 4290,
    torque: 52.7,
    status: "AT RISK",
  },
  {
    id: "CNC-007",
    name: "Engine Block Boring",
    process: "Deep Hole Boring",
    health: 15,
    failure: 100,
    anomaly: 100,
    rul: 45.7,
    temperature: 91.2,
    vibration: 8.9,
    toolWear: 94.6,
    rpm: 3910,
    torque: 67.3,
    status: "CRITICAL",
  },
  {
    id: "CNC-008",
    name: "Brake Disc Cell",
    process: "Surface Grinding",
    health: 94,
    failure: 6,
    anomaly: 8,
    rul: 312,
    temperature: 61.8,
    vibration: 1.8,
    toolWear: 12,
    rpm: 4720,
    torque: 38.7,
    status: "HEALTHY",
  },
];

const history = [
  78, 80, 79, 81, 77, 75, 73, 74, 71, 68, 66, 64, 61, 59, 56, 53, 51, 48,
];

const emptyForm: SensorForm = {
  machineId: "CNC-001",

  component: "Engine Block",
  operation: "Milling",

  airTemperature: "298.5",
  processTemperature: "308.2",

  rpm: "4500",
  current: "4.2",
  torque: "42",

  vibrationX: "2.1",
  vibrationY: "1.9",
  vibrationZ: "1.8",

  pressure: "1.8",
  cuttingForce: "420",
  acousticEmission: "21",

  toolWear: "18",
  toolAge: "180",
};

/* =========================================================
   DISPLAY HELPERS
========================================================= */

function formatFailure(value: number) {
  if (value < 1) {
    return value.toFixed(2);
  }

  return String(Number(value.toFixed(1)));
}

/*
 * ANOMALY DISPLAY
 *
 * Backend anomalyRatio =
 *
 * anomaly_score / anomaly_threshold
 *
 * Instead of directly multiplying the ratio by 100
 * and immediately capping values above 100%,
 * we normalize the ratio continuously.
 *
 * Examples:
 *
 * 0.10x -> 9.1%
 * 0.50x -> 33.3%
 * 1.00x -> 50.0%
 * 2.00x -> 66.7%
 * 5.77x -> 85.2%
 * 10.00x -> 90.9%
 *
 * This keeps the anomaly severity between 0% and 100%
 * while still allowing different machines to show
 * different anomaly values.
 *
 * Static machines continue displaying their
 * existing anomaly percentage.
 */

function formatAnomaly(machine: Machine) {
  if (machine.anomalyRatio !== undefined) {
    const ratio = Math.max(0, machine.anomalyRatio);

    const percentage =
      ratio > 0
        ? (ratio / (1 + ratio)) * 100
        : 0;

    return `${Math.min(
      100,
      Math.max(0, percentage)
    ).toFixed(1)}%`;
  }

  return `${String(
    Number(machine.anomaly.toFixed(1))
  )}%`;
}

function App() {
  const [machines, setMachines] = useState(initialMachines);
  const [selectedId, setSelectedId] = useState("CNC-007");
  const [activePage, setActivePage] = useState("Overview");

  const [analyzing, setAnalyzing] = useState(false);
  const [showAlert, setShowAlert] = useState(false);

  const [form, setForm] = useState<SensorForm>(emptyForm);
  const [analysisResult, setAnalysisResult] =
    useState<Machine | null>(null);

  const selected = useMemo(
    () =>
      machines.find(
        (machine) =>
          machine.id === selectedId
      )!,
    [machines, selectedId]
  );

  const healthy = machines.filter(
    (m) => m.status === "HEALTHY"
  ).length;

  const atRisk = machines.filter(
    (m) => m.status === "AT RISK"
  ).length;

  const critical = machines.filter(
    (m) => m.status === "CRITICAL"
  ).length;

  const navigate = (page: string) => {
    setActivePage(page);
    setShowAlert(false);
  };

  const selectMachine = (id: string) => {
    setSelectedId(id);
    setShowAlert(false);

    const machine = machines.find(
      (m) => m.id === id
    );

    if (machine) {
      setForm({
        machineId: machine.id,

        component:
          machine.name.includes("Engine")
            ? "Engine Block"
            : "Automotive Component",

        operation: machine.process,

        airTemperature: (
          machine.temperature + 273.15
        ).toFixed(1),

        processTemperature: (
          machine.temperature +
          10 +
          273.15
        ).toFixed(1),

        rpm: String(machine.rpm),

        current: "4.2",

        torque: String(
          machine.torque
        ),

        vibrationX: String(
          machine.vibration
        ),

        vibrationY: (
          machine.vibration * 0.92
        ).toFixed(2),

        vibrationZ: (
          machine.vibration * 0.84
        ).toFixed(2),

        pressure: "1.8",

        cuttingForce: String(
          Math.round(
            machine.torque * 10
          )
        ),

        acousticEmission: String(
          Math.round(
            machine.vibration * 10
          )
        ),

        toolWear: String(
          machine.toolWear
        ),

        toolAge: String(
          Math.round(
            machine.toolWear * 10
          )
        ),
      });
    }
  };

  /*
   * =========================================================
   * RUN BACKEND ANALYSIS
   * =========================================================
   */

  const runBackendAnalysis = async () => {
    setAnalyzing(true);
    setShowAlert(false);

    try {
      const response = await fetch(
        `${API_URL}/analyze`,
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json",
          },

          body: JSON.stringify(
            buildBackendPayload(form)
          ),
        }
      );

      if (!response.ok) {
        throw new Error(
          `Backend returned ${response.status}`
        );
      }

      const data =
        await response.json();

      const result =
        convertBackendResult(
          data,
          form
        );

      setAnalysisResult(result);

      setMachines((current) => {
        const exists =
          current.some(
            (machine) =>
              machine.id === result.id
          );

        if (exists) {
          return current.map(
            (machine) =>
              machine.id === result.id
                ? {
                    ...machine,
                    ...result,
                  }
                : machine
          );
        }

        return [
          ...current,
          result,
        ];
      });

      setSelectedId(result.id);

      setShowAlert(true);
    } catch (error) {
      console.error(
        "FORTRESS backend error:",
        error
      );

      alert(
        "Unable to connect to the FORTRESS AI backend. Please make sure the FastAPI server is running."
      );
    } finally {
      setAnalyzing(false);
    }
  };

  /*
   * =========================================================
   * RUN MACHINE ANALYSIS
   * =========================================================
   */

  const runMachineAnalysis = async () => {
    setAnalysisResult(null);

    await runBackendAnalysis();
  };

  /*
   * =========================================================
   * STATUS
   * =========================================================
   */

  

  return (
    <div className="app-shell">

      <div className="scanline" />

      {/* TOP BAR */}

      <header className="topbar">

        <div className="brand">

          <div className="brand-mark">
            <span />
            <span />
            <span />
          </div>

          <div>

            <div className="brand-name">
              FORTRESS
            </div>

            <div className="brand-sub">
              FAILURE OBSERVATION & RISK TRACKING
              FOR RELIABLE EQUIPMENT SAFETY &
              SUSTAINABILITY
            </div>

          </div>

        </div>

        <div className="system-status">

          <span className="pulse-dot" />

          AI ENGINE ONLINE

          <span className="status-divider" />

          INDUSTRIAL MONITORING

        </div>

        <div className="top-time">

          <span>LIVE</span>

          <strong>
            {new Date().toLocaleTimeString()}
          </strong>

        </div>

      </header>

      <div className="layout">

        {/* SIDEBAR */}

        <aside className="sidebar">

          <div className="sidebar-title">
            WORKSPACE
          </div>

          {[
            ["Overview", "◈"],
            ["Analyze Machine", "⌁"],
            ["CNC Fleet", "▦"],
            ["AI Analytics", "◇"],
            ["Maintenance", "⚙"],
            ["History", "◷"],
          ].map(([page, icon]) => (

            <button
              key={page}
              className={`nav-item ${
                activePage === page
                  ? "active"
                  : ""
              }`}
              onClick={() =>
                navigate(page)
              }
            >

              <span className="nav-icon">
                {icon}
              </span>

              {page}

            </button>

          ))}

          <div className="sidebar-divider" />

          <div className="sidebar-section-label">
            SYSTEM
          </div>

          <div className="system-item">

            <span>●</span>

            Sensor Network

            <b>ONLINE</b>

          </div>

          <div className="system-item">

            <span>●</span>

            AI Inference

            <b>READY</b>

          </div>

          <div className="system-item">

            <span>●</span>

            Data Pipeline

            <b>ACTIVE</b>

          </div>

          <div className="sidebar-footer">

            <div>
              FORTRESS v1.0
            </div>

            <span>
              Predictive Maintenance Intelligence
            </span>

          </div>

        </aside>

        {/* MAIN */}

        <main className="main">

          {/* =================================================
              OVERVIEW
          ================================================= */}

          {activePage === "Overview" && (
            <>

              <section className="hero">

                <div>

                  <div className="eyebrow">
                    AUTOMOTIVE CNC INTELLIGENCE PLATFORM
                  </div>

                  <h1>
                    Predict the failure.
                    <br />
                    <span>
                      Prevent the downtime.
                    </span>
                  </h1>

                  <p>
                    Deep Learning powered predictive
                    maintenance for intelligent CNC
                    manufacturing environments.
                  </p>

                  <button
                    className="analyze-button"
                    onClick={() =>
                      navigate(
                        "Analyze Machine"
                      )
                    }
                  >

                    <span>
                      ANALYZE A MACHINE
                    </span>

                    <b>↗</b>

                  </button>

                </div>

                <div className="hero-orb">

                  <div className="orb-ring ring-one" />
                  <div className="orb-ring ring-two" />
                  <div className="orb-ring ring-three" />

                  <div className="orb-core">
                    <span>AI</span>
                  </div>

                </div>

              </section>

              <section className="metric-grid">

                <Metric
                  label="MACHINES MONITORED"
                  value={machines.length}
                  suffix=""
                  icon="⌁"
                />

                <Metric
                  label="HEALTHY"
                  value={healthy}
                  suffix=""
                  icon="✓"
                  type="healthy"
                />

                <Metric
                  label="AT RISK"
                  value={atRisk}
                  suffix=""
                  icon="!"
                  type="warning"
                />

                <Metric
                  label="CRITICAL"
                  value={critical}
                  suffix=""
                  icon="×"
                  type="critical"
                />

                <Metric
                  label="AI CONFIDENCE"
                  value={97.4}
                  suffix="%"
                  icon="✦"
                />

              </section>

              <section className="content-grid">

                <div className="panel machine-panel">

                  <PanelHeader
                    title="CNC FLEET"
                    subtitle="REAL-TIME MACHINE HEALTH"
                    action={`${machines.length} UNITS`}
                  />

                  <div className="machine-list">

                    {machines.map(
                      (machine) => (

                        <button
                          key={machine.id}
                          className={`machine-row ${
                            selectedId ===
                            machine.id
                              ? "selected"
                              : ""
                          }`}
                          onClick={() => {

                            selectMachine(
                              machine.id
                            );

                            navigate(
                              "CNC Fleet"
                            );

                          }}
                        >

                          <div className="machine-status">

                            <span
                              className={`machine-dot ${machine.status
                                .toLowerCase()
                                .replace(
                                  " ",
                                  "-"
                                )}`}
                            />

                          </div>

                          <div className="machine-info">

                            <strong>
                              {machine.id}
                            </strong>

                            <span>
                              {machine.name}
                            </span>

                          </div>

                          <div className="machine-health">

                            <div className="health-bar">

                              <div
                                style={{
                                  width: `${machine.health}%`,
                                }}
                              />

                            </div>

                            <strong>
                              {machine.health}%
                            </strong>

                          </div>

                          <div
                            className={`machine-state ${machine.status
                              .toLowerCase()
                              .replace(
                                " ",
                                "-"
                              )}`}
                          >
                            {machine.status}
                          </div>

                          <div className="machine-arrow">
                            →
                          </div>

                        </button>

                      )
                    )}

                  </div>

                </div>

                <MachineHealthPanel
                  selected={selected}
                />

              </section>

              <AIOverview
                history={history}
              />

            </>
          )}

          {/* =================================================
              ANALYZE MACHINE
          ================================================= */}

          {activePage === "Analyze Machine" && (
            <>

              <PageTitle
                eyebrow="LIVE MACHINE ANALYSIS"
                title="Analyze Machine"
                description="Enter the current CNC sensor readings and run the FORTRESS AI prediction pipeline."
              />

              <section className="panel input-panel">

                <PanelHeader
                  title="MACHINE SENSOR INPUT"
                  subtitle="ENTER CURRENT OPERATING CONDITIONS"
                  action="12 PARAMETERS"
                />

                <div className="input-grid">

                  <InputField
                    label="MACHINE ID"
                    value={form.machineId}
                    onChange={(value) =>
                      setForm({
                        ...form,
                        machineId: value,
                      })
                    }
                  />

                  <InputField
                    label="COMPONENT"
                    value={form.component}
                    onChange={(value) =>
                      setForm({
                        ...form,
                        component: value,
                      })
                    }
                  />

                  <InputField
                    label="OPERATION"
                    value={form.operation}
                    onChange={(value) =>
                      setForm({
                        ...form,
                        operation: value,
                      })
                    }
                  />

                  <InputField
                    label="AIR TEMPERATURE"
                    value={
                      form.airTemperature
                    }
                    unit="K"
                    onChange={(value) =>
                      setForm({
                        ...form,
                        airTemperature:
                          value,
                      })
                    }
                  />

                  <InputField
                    label="PROCESS TEMPERATURE"
                    value={
                      form.processTemperature
                    }
                    unit="K"
                    onChange={(value) =>
                      setForm({
                        ...form,
                        processTemperature:
                          value,
                      })
                    }
                  />

                  <InputField
                    label="SPINDLE SPEED"
                    value={form.rpm}
                    unit="RPM"
                    onChange={(value) =>
                      setForm({
                        ...form,
                        rpm: value,
                      })
                    }
                  />

                  <InputField
                    label="SPINDLE CURRENT"
                    value={form.current}
                    unit="A"
                    onChange={(value) =>
                      setForm({
                        ...form,
                        current: value,
                      })
                    }
                  />

                  <InputField
                    label="TORQUE"
                    value={form.torque}
                    unit="Nm"
                    onChange={(value) =>
                      setForm({
                        ...form,
                        torque: value,
                      })
                    }
                  />

                  <InputField
                    label="VIBRATION X"
                    value={
                      form.vibrationX
                    }
                    unit="mm/s"
                    onChange={(value) =>
                      setForm({
                        ...form,
                        vibrationX: value,
                      })
                    }
                  />

                  <InputField
                    label="VIBRATION Y"
                    value={
                      form.vibrationY
                    }
                    unit="mm/s"
                    onChange={(value) =>
                      setForm({
                        ...form,
                        vibrationY: value,
                      })
                    }
                  />

                  <InputField
                    label="VIBRATION Z"
                    value={
                      form.vibrationZ
                    }
                    unit="mm/s"
                    onChange={(value) =>
                      setForm({
                        ...form,
                        vibrationZ: value,
                      })
                    }
                  />

                  <InputField
                    label="COOLANT PRESSURE"
                    value={form.pressure}
                    unit="bar"
                    onChange={(value) =>
                      setForm({
                        ...form,
                        pressure: value,
                      })
                    }
                  />

                  <InputField
                    label="CUTTING FORCE"
                    value={
                      form.cuttingForce
                    }
                    unit="N"
                    onChange={(value) =>
                      setForm({
                        ...form,
                        cuttingForce:
                          value,
                      })
                    }
                  />

                  <InputField
                    label="ACOUSTIC EMISSION"
                    value={
                      form.acousticEmission
                    }
                    unit="AE"
                    onChange={(value) =>
                      setForm({
                        ...form,
                        acousticEmission:
                          value,
                      })
                    }
                  />

                  <InputField
                    label="TOOL WEAR"
                    value={
                      form.toolWear
                    }
                    unit="%"
                    onChange={(value) =>
                      setForm({
                        ...form,
                        toolWear: value,
                      })
                    }
                  />

                  <InputField
                    label="TOOL AGE"
                    value={
                      form.toolAge
                    }
                    unit="hrs"
                    onChange={(value) =>
                      setForm({
                        ...form,
                        toolAge: value,
                      })
                    }
                  />

                </div>

                <div className="analysis-run-area">

                  <div>

                    <span>
                      AI PIPELINE
                    </span>

                    <strong>
                      ANN → AUTOENCODER → LSTM
                      → RISK ENGINE
                    </strong>

                  </div>

                  <button
                    className={`analyze-button ${
                      analyzing
                        ? "loading"
                        : ""
                    }`}
                    onClick={
                      runMachineAnalysis
                    }
                    disabled={analyzing}
                  >

                    <span>

                      {analyzing
                        ? "RUNNING AI ANALYSIS..."
                        : "⚡ RUN AI ANALYSIS"}

                    </span>

                    <b>↗</b>

                  </button>

                </div>

              </section>

              {analyzing && (
                <section className="panel processing-panel">

                  <div className="processing-animation">
                    <div className="processing-orb" />
                  </div>

                  <div>

                    <span>
                      FORTRESS AI ENGINE
                    </span>

                    <strong>
                      Analyzing machine state...
                    </strong>

                    <p>
                      Processing sensor values
                      through the predictive
                      maintenance pipeline.
                    </p>

                  </div>

                </section>
              )}

              {analysisResult &&
                !analyzing && (
                  <AnalysisResult
                    result={analysisResult}
                  />
                )}

              {!analysisResult &&
                !analyzing && (
                  <section className="panel empty-analysis">

                    <div className="empty-icon">
                      ◈
                    </div>

                    <h2>
                      READY FOR ANALYSIS
                    </h2>

                    <p>
                      Enter the current CNC
                      machine readings above
                      and run the AI engine to
                      generate failure
                      probability, anomaly
                      score, RUL and health
                      status.
                    </p>

                  </section>
                )}

            </>
          )}

          {/* =================================================
              CNC FLEET
          ================================================= */}

          {activePage === "CNC Fleet" && (
            <>

              <PageTitle
                eyebrow="AUTOMOTIVE CNC MONITORING"
                title="CNC Fleet"
                description="Monitor the health and operating condition of every connected automotive CNC machine."
              />

              <section className="metric-grid">

                <Metric
                  label="TOTAL MACHINES"
                  value={machines.length}
                  suffix=""
                  icon="⌁"
                />

                <Metric
                  label="HEALTHY"
                  value={healthy}
                  suffix=""
                  icon="✓"
                  type="healthy"
                />

                <Metric
                  label="AT RISK"
                  value={atRisk}
                  suffix=""
                  icon="!"
                  type="warning"
                />

                <Metric
                  label="CRITICAL"
                  value={critical}
                  suffix=""
                  icon="×"
                  type="critical"
                />

              </section>

              <section className="panel fleet-full">

                <PanelHeader
                  title="MACHINE FLEET"
                  subtitle="SELECT A MACHINE TO INSPECT"
                  action={`${machines.length} CONNECTED`}
                />

                <div className="fleet-grid">

                  {machines.map(
                    (machine) => (

                      <button
                        key={machine.id}
                        className={`fleet-card ${
                          selectedId ===
                          machine.id
                            ? "selected"
                            : ""
                        }`}
                        onClick={() =>
                          selectMachine(
                            machine.id
                          )
                        }
                      >

                        <div className="fleet-card-top">

                          <span
                            className={`machine-dot ${machine.status
                              .toLowerCase()
                              .replace(
                                " ",
                                "-"
                              )}`}
                          />

                          <strong>
                            {machine.id}
                          </strong>

                          <span
                            className={`machine-state ${machine.status
                              .toLowerCase()
                              .replace(
                                " ",
                                "-"
                              )}`}
                          >
                            {machine.status}
                          </span>

                        </div>

                        <h3>
                          {machine.name}
                        </h3>

                        <p>
                          {machine.process}
                        </p>

                        <div className="fleet-health">

                          <span>
                            HEALTH
                          </span>

                          <strong>
                            {machine.health}%
                          </strong>

                        </div>

                        <div className="health-bar">

                          <div
                            style={{
                              width: `${machine.health}%`,
                            }}
                          />

                        </div>

                        <div className="fleet-mini">

                          <span>

                            FAILURE{" "}

                            <b>
                              {formatFailure(
                                machine.failure
                              )}
                              %
                            </b>

                          </span>

                          <span>

                            ANOMALY{" "}

                            <b>
                              {formatAnomaly(
                                machine
                              )}
                            </b>

                          </span>

                          <span>

                            RUL{" "}

                            <b>
                              {machine.rul}h
                            </b>

                          </span>

                        </div>

                      </button>
                    )
                  )}

                </div>

              </section>

              <section className="content-grid">

                <MachineHealthPanel
                  selected={selected}
                />

                <div className="panel machine-analysis">

                  <PanelHeader
                    title={`SELECTED MACHINE / ${selected.id}`}
                    subtitle={selected.process.toUpperCase()}
                    action="LIVE"
                  />

                  <div className="analysis-grid">

                    <Sensor
                      label="RPM"
                      value={selected.rpm}
                      unit="rpm"
                      percent={72}
                    />

                    <Sensor
                      label="TORQUE"
                      value={selected.torque}
                      unit="Nm"
                      percent={68}
                    />

                    <Sensor
                      label="TEMPERATURE"
                      value={
                        selected.temperature
                      }
                      unit="°C"
                      percent={82}
                    />

                    <Sensor
                      label="VIBRATION"
                      value={
                        selected.vibration
                      }
                      unit="mm/s"
                      percent={88}
                    />

                    <Sensor
                      label="TOOL WEAR"
                      value={
                        selected.toolWear
                      }
                      unit="%"
                      percent={
                        selected.toolWear
                      }
                    />

                  </div>

                  <button
                    className="analyze-button"
                    onClick={() =>
                      navigate(
                        "Analyze Machine"
                      )
                    }
                  >

                    <span>
                      OPEN MACHINE ANALYSIS
                    </span>

                    <b>↗</b>

                  </button>

                </div>

              </section>

            </>
          )}

          {/* =================================================
              AI ANALYTICS
          ================================================= */}

          {activePage === "AI Analytics" && (
            <>

              <PageTitle
                eyebrow="DEEP LEARNING ENGINE"
                title="AI Analytics"
                description="Understand how FORTRESS converts CNC sensor signals into predictive maintenance decisions."
              />

              <section className="panel pipeline-panel">

                <PanelHeader
                  title="FORTRESS AI PIPELINE"
                  subtitle="MULTI-TASK DEEP LEARNING ENGINE"
                  action="3 MODELS"
                />

                <div className="pipeline">

                  <PipelineNode
                    number="01"
                    title="SENSOR INPUT"
                    text="Industrial CNC parameters"
                    icon="◉"
                  />

                  <PipelineArrow />

                  <PipelineNode
                    number="02"
                    title="ANN"
                    text="Failure probability"
                    icon="⌁"
                    active
                  />

                  <PipelineArrow />

                  <PipelineNode
                    number="03"
                    title="AUTOENCODER"
                    text="Anomaly detection"
                    icon="◇"
                    active
                  />

                  <PipelineArrow />

                  <PipelineNode
                    number="04"
                    title="LSTM"
                    text="Remaining useful life"
                    icon="∿"
                    active
                  />

                  <PipelineArrow />

                  <PipelineNode
                    number="05"
                    title="RISK ENGINE"
                    text="Health decision"
                    icon="◆"
                    active
                  />

                </div>

              </section>

              <section className="content-grid">

                <div className="panel analytics-models">

                  <PanelHeader
                    title="MODEL OUTPUTS"
                    subtitle="CURRENT SELECTED MACHINE"
                    action={selected.id}
                  />

                  <Prediction
                    title="FAILURE PREDICTION"
                    model="ANN"
                    value={
                      selected.failure
                    }
                    suffix="%"
                    description="Probability of machine failure"
                  />

                  <Prediction
                    title="ANOMALY DETECTION"
                    model="DEEP AUTOENCODER"
                    value={
                      selected.anomaly
                    }
                    suffix="%"
                    isAnomaly={
                      selected.anomalyRatio !==
                      undefined
                    }
                    description="Deviation from learned normal threshold"
                  />

                  <Prediction
                    title="REMAINING USEFUL LIFE"
                    model="LSTM"
                    value={selected.rul}
                    suffix=" hrs"
                    description="Estimated remaining operational lifetime"
                  />

                </div>

                <div className="panel chart-panel">

                  <PanelHeader
                    title="HEALTH TREND"
                    subtitle="DEGRADATION ANALYSIS"
                    action="18 SAMPLES"
                  />

                  <HealthChart
                    history={history}
                  />

                </div>

              </section>

              <section className="metric-grid">

                <Metric
                  label="ANN ACCURACY"
                  value={99.11}
                  suffix="%"
                  icon="✦"
                />

                <Metric
                  label="ANN ROC-AUC"
                  value={99.96}
                  suffix="%"
                  icon="⌁"
                />

                <Metric
                  label="AUTOENCODER ROC-AUC"
                  value={99.84}
                  suffix="%"
                  icon="◇"
                />

                <Metric
                  label="ACTIVE MODELS"
                  value={3}
                  suffix=""
                  icon="◆"
                />

              </section>

            </>
          )}

          {/* =================================================
              MAINTENANCE
          ================================================= */}

          {activePage === "Maintenance" && (
            <>

              <PageTitle
                eyebrow="PREDICTIVE MAINTENANCE"
                title="Maintenance"
                description="Machines requiring attention based on current predicted risk and degradation."
              />

              <section className="panel maintenance-panel">

                <PanelHeader
                  title="MAINTENANCE QUEUE"
                  subtitle="AI GENERATED PRIORITIES"
                  action={`${critical + atRisk} MACHINES`}
                />

                <div className="maintenance-list">

                  {[...machines]
                    .filter(
                      (machine) =>
                        machine.status ===
                          "CRITICAL" ||
                        machine.status ===
                          "AT RISK"
                    )
                    .sort(
                      (a, b) =>
                        a.health -
                        b.health
                    )
                    .map(
                      (machine) => (

                        <div
                          className="maintenance-row"
                          key={machine.id}
                        >

                          <div
                            className={`maintenance-icon ${machine.status
                              .toLowerCase()
                              .replace(
                                " ",
                                "-"
                              )}`}
                          >

                            {machine.status ===
                            "CRITICAL"
                              ? "!"
                              : "◇"}

                          </div>

                          <div className="maintenance-machine">

                            <strong>
                              {machine.id}
                            </strong>

                            <span>
                              {machine.name}
                            </span>

                          </div>

                          <div>

                            <span className="maintenance-label">
                              FAILURE RISK
                            </span>

                            <strong>
                              {formatFailure(
                                machine.failure
                              )}
                              %
                            </strong>

                          </div>

                          <div>

                            <span className="maintenance-label">
                              RUL
                            </span>

                            <strong>
                              {machine.rul}h
                            </strong>

                          </div>

                          <div className="maintenance-recommendation">

                            {machine.status ===
                            "CRITICAL"
                              ? "Immediate inspection recommended. Consider planned shutdown."
                              : "Schedule preventive inspection and monitor degradation."}

                          </div>

                          <button
                            className="small-action"
                            onClick={() => {

                              selectMachine(
                                machine.id
                              );

                              navigate(
                                "Analyze Machine"
                              );

                            }}
                          >
                            ANALYZE
                          </button>

                        </div>
                      )
                    )}

                </div>

              </section>

            </>
          )}

          {/* =================================================
              HISTORY
          ================================================= */}

          {activePage === "History" && (
            <>

              <PageTitle
                eyebrow="ANALYSIS HISTORY"
                title="History"
                description="Review the recent predictive-maintenance analysis trend."
              />

              <section className="content-grid">

                <div className="panel chart-panel large-chart">

                  <PanelHeader
                    title="HEALTH HISTORY"
                    subtitle="RECENT MACHINE CONDITION"
                    action="18 SAMPLES"
                  />

                  <HealthChart
                    history={history}
                  />

                </div>

                <div className="panel history-summary">

                  <PanelHeader
                    title="LATEST ANALYSIS"
                    subtitle={selected.id}
                    action="RECENT"
                  />

                  <div className="history-value">

                    <span>
                      CURRENT HEALTH
                    </span>

                    <strong>
                      {selected.health}%
                    </strong>

                  </div>

                  <div className="history-item">

                    <span>
                      Failure probability
                    </span>

                    <b>
                      {formatFailure(
                        selected.failure
                      )}
                      %
                    </b>

                  </div>

                  <div className="history-item">

                    <span>
                      Anomaly score
                    </span>

                    <b>
                      {formatAnomaly(
                        selected
                      )}
                    </b>

                  </div>

                  <div className="history-item">

                    <span>
                      Remaining useful life
                    </span>

                    <b>
                      {selected.rul} hrs
                    </b>

                  </div>

                  <div className="history-item">

                    <span>
                      Machine status
                    </span>

                    <b>
                      {selected.status}
                    </b>

                  </div>

                </div>

              </section>

            </>
          )}

          {/* =================================================
              OVERVIEW AI ANALYSIS
          ================================================= */}

          {activePage === "Overview" && (
            <section className="panel machine-analysis">

              <PanelHeader
                title={`AI ANALYSIS / ${selected.id}`}
                subtitle="MULTI-SENSOR MACHINE STATE"
                action="DEEP LEARNING"
              />

              <div className="analysis-grid">

                <Sensor
                  label="RPM"
                  value={selected.rpm}
                  unit="rpm"
                  percent={72}
                />

                <Sensor
                  label="TORQUE"
                  value={selected.torque}
                  unit="Nm"
                  percent={68}
                />

                <Sensor
                  label="TEMPERATURE"
                  value={
                    selected.temperature
                  }
                  unit="°C"
                  percent={82}
                />

                <Sensor
                  label="VIBRATION"
                  value={
                    selected.vibration
                  }
                  unit="mm/s"
                  percent={88}
                />

                <Sensor
                  label="TOOL WEAR"
                  value={
                    selected.toolWear
                  }
                  unit="%"
                  percent={
                    selected.toolWear
                  }
                />

              </div>

              <div className="prediction-row">

                <Prediction
                  title="FAILURE PREDICTION"
                  model="ANN"
                  value={
                    selected.failure
                  }
                  suffix="%"
                  description="Probability of machine failure"
                />

                <Prediction
                  title="ANOMALY DETECTION"
                  model="DEEP AUTOENCODER"
                  value={
                    selected.anomaly
                  }
                  suffix="%"
                  isAnomaly={
                    selected.anomalyRatio !==
                    undefined
                  }
                  description="Deviation from normal threshold"
                />

                <Prediction
                  title="REMAINING USEFUL LIFE"
                  model="LSTM"
                  value={selected.rul}
                  suffix=" hrs"
                  description="Estimated operational lifetime"
                />

              </div>

              <div className="analysis-action">

                <div className="recommendation">

                  <div className="recommendation-icon">
                    ⚠
                  </div>

                  <div>

                    <span>
                      MAINTENANCE RECOMMENDATION
                    </span>

                    <strong>

                      {selected.status ===
                      "CRITICAL"
                        ? "Immediate inspection recommended. Consider planned machine shutdown."
                        : selected.status ===
                          "AT RISK"
                        ? "Schedule preventive inspection and monitor machine degradation."
                        : "Continue operation. Maintain normal monitoring schedule."}

                    </strong>

                  </div>

                </div>

                <button
                  className={`analyze-button ${
                    analyzing
                      ? "loading"
                      : ""
                  }`}
                  onClick={
                    runBackendAnalysis
                  }
                  disabled={analyzing}
                >

                  <span>

                    {analyzing
                      ? "ANALYZING..."
                      : "RUN AI ANALYSIS"}

                  </span>

                  <b>↗</b>

                </button>

              </div>

              {showAlert && (
                <div className="analysis-complete">

                  ✓ AI analysis completed —
                  prediction engine updated

                </div>
              )}

            </section>
          )}

          <footer>

            <span>
              FORTRESS — Failure Observation
              and Risk Tracking for Reliable
              Equipment Safety and Sustainability
            </span>

            <span>
              DEEP LEARNING • PREDICTIVE
              MAINTENANCE • INDUSTRY 4.0
            </span>

          </footer>

        </main>

      </div>

    </div>
  );
}

/* =========================================================
   BACKEND PAYLOAD
========================================================= */

function buildBackendPayload(
  form: SensorForm
) {

  const processTemperatureC =
    (
      Number(
        form.processTemperature
      ) || 300
    ) - 273.15;

  return {

    machine_id:
      form.machineId ||
      "CUSTOM-CNC",

    component:
      form.component ||
      "Engine Block",

    operation:
      form.operation ||
      "Milling",

    sensor_data: {

      spindle_speed_rpm:
        Number(form.rpm) || 0,

      spindle_current_a:
        Number(form.current) || 0,

      torque_nm:
        Number(form.torque) || 0,

      vibration_x:
        Number(form.vibrationX) || 0,

      vibration_y:
        Number(form.vibrationY) || 0,

      vibration_z:
        Number(form.vibrationZ) || 0,

      temperature_c:
        processTemperatureC,

      coolant_pressure_bar:
        Number(form.pressure) || 0,

      cutting_force_n:
        Number(form.cuttingForce) || 0,

      acoustic_emission:
        Number(form.acousticEmission) || 0,

      tool_wear_percent:
        Number(form.toolWear) || 0,

      tool_age_hours:
        Number(form.toolAge) || 0,

    },

  };
}

/* =========================================================
   BACKEND RESULT CONVERTER
========================================================= */

function convertBackendResult(
  data: any,
  form: SensorForm
): Machine {

  const analysis =
    data?.analysis ?? {};

  /*
   * =========================================================
   * FAILURE PROBABILITY
   * =========================================================
   */

  const failureProbability =
    Number(
      analysis.failure_probability ?? 0
    );

  const failure =
    failureProbability <= 1
      ? failureProbability * 100
      : failureProbability;

  /*
   * =========================================================
   * ANOMALY
   * =========================================================
   *
   * Backend gives:
   *
   * anomaly_score
   *
   * and:
   *
   * anomaly_threshold
   *
   * We calculate:
   *
   * anomalyRatio =
   * anomaly_score / anomaly_threshold
   *
   * Then normalize the ratio continuously:
   *
   * ratio / (1 + ratio) * 100
   *
   * Examples:
   *
   * 0.10x -> 9.1%
   * 0.50x -> 33.3%
   * 1.00x -> 50.0%
   * 2.00x -> 66.7%
   * 5.77x -> 85.2%
   *
   * This prevents every value above the threshold
   * from becoming 100%.
   */

  const anomalyScore =
    Number(
      analysis.anomaly_score ?? 0
    );

  const anomalyThreshold =
    Number(
      analysis.anomaly_threshold ?? 1
    );

  const anomalyRatio =
    anomalyThreshold > 0
      ? anomalyScore /
        anomalyThreshold
      : 0;

  const anomalyPercentage =
    anomalyRatio > 0
      ? (
          anomalyRatio /
          (1 + anomalyRatio)
        ) * 100
      : 0;

  /*
   * =========================================================
   * HEALTH
   * =========================================================
   */

  const rawHealth =
    Number(
      analysis.health_score ?? 0
    );

  /*
   * Keep health inside the valid
   * 0–100 range.
   */

  const health =
    Math.max(
      0,
      Math.min(
        100,
        rawHealth
      )
    );

  /*
   * =========================================================
   * RUL
   * =========================================================
   */

  const rul =
    Number(
      analysis.rul_hours ?? 0
    );

  /*
   * =========================================================
   * STATUS
   * =========================================================
   *
   * STATUS IS BASED ONLY ON HEALTH SCORE.
   *
   * HEALTH > 80
   *       -> HEALTHY
   *
   * HEALTH 40–80
   *       -> AT RISK
   *
   * HEALTH < 40
   *       -> CRITICAL
   *
   * Therefore:
   *
   * 100 -> HEALTHY
   * 91  -> HEALTHY
   * 81  -> HEALTHY
   * 80  -> AT RISK
   * 79  -> AT RISK
   * 40  -> AT RISK
   * 39  -> CRITICAL
   * 20  -> CRITICAL
   * 0   -> CRITICAL
   */

  let status: Status;

  if (health > 80) {

    status = "HEALTHY";

  } else if (health >= 40) {

    status = "AT RISK";

  } else {

    status = "CRITICAL";

  }

  /*
   * =========================================================
   * TEMPERATURE
   * =========================================================
   */

  const temperature =
    (
      Number(
        form.processTemperature
      ) || 300
    ) - 273.15;

  /*
   * =========================================================
   * RETURN
   * =========================================================
   */

  return {

    id:
      data?.machine_id ||
      form.machineId ||
      "CUSTOM-CNC",

    name:
      data?.component ||
      "Live Sensor Analysis",

    process:
      data?.operation ||
      "Automotive CNC",

    health:
      Number(
        health.toFixed(1)
      ),

    failure:
      Math.max(
        0,
        Math.min(
          100,
          failure
        )
      ),

    anomaly:
      Number(
        anomalyPercentage.toFixed(1)
      ),

    anomalyRatio:
      anomalyRatio,

    rul:
      Number(
        rul.toFixed(1)
      ),

    temperature:
      Number(
        temperature.toFixed(1)
      ),

    vibration:
      Number(
        form.vibrationX
      ) || 0,

    toolWear:
      Number(
        form.toolWear
      ) || 0,

    rpm:
      Number(
        form.rpm
      ) || 0,

    torque:
      Number(
        form.torque
      ) || 0,

    status,

  };
}

/* =========================================================
   PAGE TITLE
========================================================= */

function PageTitle({
  eyebrow,
  title,
  description,
}: {
  eyebrow: string;
  title: string;
  description: string;
}) {

  return (
    <section className="page-title">

      <div className="eyebrow">
        {eyebrow}
      </div>

      <h1>
        {title}
      </h1>

      <p>
        {description}
      </p>

    </section>
  );
}

/* =========================================================
   MACHINE HEALTH
========================================================= */

function MachineHealthPanel({
  selected,
}: {
  selected: Machine;
}) {

  const statusClass =
    selected.status
      .toLowerCase()
      .replace(" ", "-");

  return (
    <div className="panel health-panel">

      <PanelHeader
        title="MACHINE HEALTH"
        subtitle={
          selected.id +
          " / " +
          selected.process.toUpperCase()
        }
        action="LIVE"
      />

      <div className="health-main">

        <div
          className={`health-ring ${statusClass}`}
        >

          <div className="health-ring-inner">

            <span>
              HEALTH
            </span>

            <strong>
              {selected.health}%
            </strong>

          </div>

        </div>

        <div className="health-summary">

          <div
            className={`large-status ${statusClass}`}
          >
            {selected.status}
          </div>

          <p>

            {selected.status ===
            "CRITICAL"
              ? "Abnormal operating behavior detected. Immediate maintenance attention required."
              : selected.status ===
                "AT RISK"
              ? "Degradation detected. Maintenance should be scheduled."
              : "Machine operating within normal parameters."}

          </p>

          <div className="mini-stats">

            <div>

              <span>
                FAILURE RISK
              </span>

              <strong>
                {formatFailure(
                  selected.failure
                )}
                %
              </strong>

            </div>

            <div>

              <span>
                ANOMALY
              </span>

              <strong>
                {formatAnomaly(
                  selected
                )}
              </strong>

            </div>

            <div>

              <span>
                RUL
              </span>

              <strong>
                {selected.rul}h
              </strong>

            </div>

          </div>

        </div>

      </div>

    </div>
  );
}

/* =========================================================
   AI OVERVIEW
========================================================= */

function AIOverview({
  history,
}: {
  history: number[];
}) {

  return (
    <section className="content-grid second">

      <div className="panel pipeline-panel">

        <PanelHeader
          title="FORTRESS AI PIPELINE"
          subtitle="MULTI-TASK DEEP LEARNING ENGINE"
          action="3 MODELS"
        />

        <div className="pipeline">

          <PipelineNode
            number="01"
            title="SENSOR INPUT"
            text="Industrial CNC parameters"
            icon="◉"
          />

          <PipelineArrow />

          <PipelineNode
            number="02"
            title="ANN"
            text="Failure probability"
            icon="⌁"
            active
          />

          <PipelineArrow />

          <PipelineNode
            number="03"
            title="AUTOENCODER"
            text="Anomaly detection"
            icon="◇"
            active
          />

          <PipelineArrow />

          <PipelineNode
            number="04"
            title="LSTM"
            text="Remaining useful life"
            icon="∿"
            active
          />

          <PipelineArrow />

          <PipelineNode
            number="05"
            title="RISK ENGINE"
            text="Health decision"
            icon="◆"
            active
          />

        </div>

      </div>

      <div className="panel chart-panel">

        <PanelHeader
          title="HEALTH TREND"
          subtitle="DEGRADATION ANALYSIS"
          action="18 SAMPLES"
        />

        <HealthChart
          history={history}
        />

      </div>

    </section>
  );
}

/* =========================================================
   ANALYSIS RESULT
========================================================= */

function AnalysisResult({
  result,
}: {
  result: Machine;
}) {

  const statusClass =
    result.status
      .toLowerCase()
      .replace(" ", "-");

  return (
    <section className="panel result-panel">

      <PanelHeader
        title="AI ANALYSIS COMPLETE"
        subtitle={`${result.id} / LIVE SENSOR DATA`}
        action="PREDICTION READY"
      />

      <div className="result-header">

        <div>

          <span>
            MACHINE HEALTH
          </span>

          <strong
            className={statusClass}
          >
            {result.health}%
          </strong>

        </div>

        <div
          className={`result-status ${statusClass}`}
        >
          {result.status}
        </div>

      </div>

      <div className="prediction-row">

        <Prediction
          title="FAILURE PREDICTION"
          model="ANN"
          value={
            result.failure
          }
          suffix="%"
          description="Predicted probability of machine failure"
        />

        <Prediction
          title="ANOMALY DETECTION"
          model="DEEP AUTOENCODER"
          value={
            result.anomaly
          }
          suffix="%"
          isAnomaly={true}
          description="Deviation from learned normal threshold"
        />

        <Prediction
          title="REMAINING USEFUL LIFE"
          model="LSTM"
          value={result.rul}
          suffix=" hrs"
          description="Estimated operational lifetime"
        />

      </div>

      <div className="recommendation result-recommendation">

        <div className="recommendation-icon">

          {result.status ===
          "CRITICAL"
            ? "!"
            : "◇"}

        </div>

        <div>

          <span>
            FORTRESS RECOMMENDATION
          </span>

          <strong>

            {result.status ===
            "CRITICAL"
              ? "Immediate inspection recommended. Consider planned machine shutdown."
              : result.status ===
                "AT RISK"
              ? "Schedule preventive inspection and monitor machine degradation."
              : "Continue operation with normal monitoring schedule."}

          </strong>

        </div>

      </div>

    </section>
  );
}

/* =========================================================
   INPUT FIELD
========================================================= */

function InputField({
  label,
  value,
  unit,
  onChange,
}: {
  label: string;
  value: string;
  unit?: string;
  onChange: (
    value: string
  ) => void;
}) {

  return (
    <label className="input-field">

      <span>
        {label}
      </span>

      <div className="input-wrapper">

        <input
          type="text"
          value={value}
          onChange={(event) =>
            onChange(
              event.target.value
            )
          }
        />

        {unit && (
          <small>
            {unit}
          </small>
        )}

      </div>

    </label>
  );
}

/* =========================================================
   HEALTH CHART
========================================================= */

function HealthChart({
  history,
}: {
  history: number[];
}) {

  return (
    <div className="chart">

      <div className="chart-grid">

        <span>100</span>
        <span>75</span>
        <span>50</span>
        <span>25</span>
        <span>0</span>

      </div>

      <svg
        viewBox="0 0 600 230"
        preserveAspectRatio="none"
      >

        <defs>

          <linearGradient
            id="area"
            x1="0"
            y1="0"
            x2="0"
            y2="1"
          >

            <stop
              offset="0%"
              stopColor="#00d9ff"
              stopOpacity=".30"
            />

            <stop
              offset="100%"
              stopColor="#00d9ff"
              stopOpacity="0"
            />

          </linearGradient>

        </defs>

        <polygon
          points={`0,${230 -
            history[0] * 1.9} ${history
            .map(
              (value, index) =>
                `${(index /
                  (history.length - 1)) *
                  600},${
                  230 -
                  value * 1.9
                }`
            )
            .join(" ")} 600,230 0,230`}
          fill="url(#area)"
        />

        <polyline
          points={history
            .map(
              (value, index) =>
                `${(index /
                  (history.length - 1)) *
                  600},${
                  230 -
                  value * 1.9
                }`
            )
            .join(" ")}
          fill="none"
          stroke="#00d9ff"
          strokeWidth="3"
        />

        <circle
          cx="600"
          cy={
            230 -
            history[
              history.length - 1
            ] *
              1.9
          }
          r="6"
          fill="#00d9ff"
        />

      </svg>

      <div className="chart-axis">

        <span>T-18</span>
        <span>T-12</span>
        <span>T-6</span>
        <span>NOW</span>

      </div>

    </div>
  );
}

/* =========================================================
   METRIC
========================================================= */

function Metric({
  label,
  value,
  suffix,
  icon,
  type = "",
}: {
  label: string;
  value: number;
  suffix: string;
  icon: string;
  type?: string;
}) {

  return (
    <div
      className={`metric-card ${type}`}
    >

      <div className="metric-icon">
        {icon}
      </div>

      <div>

        <span>
          {label}
        </span>

        <strong>

          {value}

          <small>
            {suffix}
          </small>

        </strong>

      </div>

    </div>
  );
}

/* =========================================================
   PANEL HEADER
========================================================= */

function PanelHeader({
  title,
  subtitle,
  action,
}: {
  title: string;
  subtitle: string;
  action: string;
}) {

  return (
    <div className="panel-header">

      <div>

        <h2>
          {title}
        </h2>

        <span>
          {subtitle}
        </span>

      </div>

      <div className="panel-action">
        {action}
      </div>

    </div>
  );
}

/* =========================================================
   PIPELINE NODE
========================================================= */

function PipelineNode({
  number,
  title,
  text,
  icon,
  active = false,
}: {
  number: string;
  title: string;
  text: string;
  icon: string;
  active?: boolean;
}) {

  return (
    <div
      className={`pipeline-node ${
        active
          ? "active"
          : ""
      }`}
    >

      <div className="pipeline-number">
        {number}
      </div>

      <div className="pipeline-icon">
        {icon}
      </div>

      <strong>
        {title}
      </strong>

      <span>
        {text}
      </span>

    </div>
  );
}

/* =========================================================
   PIPELINE ARROW
========================================================= */

function PipelineArrow() {

  return (
    <div className="pipeline-arrow">
      ›
    </div>
  );
}

/* =========================================================
   SENSOR
========================================================= */

function Sensor({
  label,
  value,
  unit,
  percent,
}: {
  label: string;
  value: number;
  unit: string;
  percent: number;
}) {

  return (
    <div className="sensor">

      <div className="sensor-top">

        <span>
          {label}
        </span>

        <strong>

          {value}

          <small>
            {unit}
          </small>

        </strong>

      </div>

      <div className="sensor-track">

        <div
          style={{
            width: `${Math.min(
              100,
              percent
            )}%`,
          }}
        />

      </div>

    </div>
  );
}

/* =========================================================
   PREDICTION
========================================================= */

function Prediction({
  title,
  model,
  value,
  suffix,
  description,
  isAnomaly = false,
}: {
  title: string;
  model: string;
  value: number;
  suffix: string;
  description: string;
  isAnomaly?: boolean;
}) {

  let formattedValue: string;

  if (isAnomaly) {

    formattedValue =
      value.toFixed(1);

  } else if (
    title ===
    "FAILURE PREDICTION"
  ) {

    formattedValue =
      value < 1
        ? value.toFixed(2)
        : value.toFixed(1);

  } else {

    formattedValue =
      value.toFixed(
        value < 100
          ? 1
          : 0
      );

  }

  const displaySuffix =
    isAnomaly
      ? "%"
      : suffix;

  let barPercent = value;

  if (isAnomaly) {

    barPercent =
      Math.min(
        100,
        Math.max(
          0,
          value
        )
      );

  } else {

    barPercent =
      Math.min(
        100,
        Math.max(
          0,
          value
        )
      );

  }

  return (
    <div className="prediction">

      <div className="prediction-head">

        <span>
          {title}
        </span>

        <b>
          {model}
        </b>

      </div>

      <strong>

        {formattedValue}

        <small>
          {displaySuffix}
        </small>

      </strong>

      <p>
        {description}
      </p>

      <div className="prediction-line">

        <div
          style={{
            width: `${barPercent}%`,
          }}
        />

      </div>

    </div>
  );
}

export default App;