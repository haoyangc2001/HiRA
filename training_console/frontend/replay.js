/* Native Canvas replay controller; no dependency on the existing webui. */

export class TrajectoryCanvas {
  constructor(canvas, options = {}) {
    this.canvas = canvas;
    this.context = canvas.getContext("2d");
    this.trajectories = [];
    this.selectedIndex = 0;
    this.frameIndex = 0;
    this.speed = options.speed || 1;
    this.playing = false;
    this.timer = null;
    this.onFrame = options.onFrame || (() => {});
  }

  setData(trajectories) {
    this.pause();
    this.trajectories = Array.isArray(trajectories) ? trajectories : [];
    this.selectedIndex = 0;
    this.reset();
  }

  selected() {
    return this.trajectories[this.selectedIndex] || { points: [], bounds: null };
  }

  select(index) {
    const next = Number(index);
    if (!Number.isInteger(next) || next < 0 || next >= this.trajectories.length) return;
    this.selectedIndex = next;
    this.reset();
  }

  setSpeed(speed) {
    const next = Number(speed);
    if (Number.isFinite(next) && next > 0) this.speed = next;
    if (this.playing) this.start();
  }

  reset() {
    this.frameIndex = 0;
    this.draw();
  }

  step(delta = 1) {
    const points = this.selected().points || [];
    this.frameIndex = Math.max(0, Math.min(Math.max(0, points.length - 1), this.frameIndex + delta));
    this.draw();
    if (this.frameIndex >= Math.max(0, points.length - 1)) this.pause();
  }

  start() {
    this.pause();
    this.playing = true;
    const interval = Math.max(16, 160 / this.speed);
    this.timer = window.setInterval(() => this.step(1), interval);
  }

  pause() {
    this.playing = false;
    if (this.timer !== null) window.clearInterval(this.timer);
    this.timer = null;
  }

  draw() {
    const context = this.context;
    const { width, height } = this.canvas;
    context.clearRect(0, 0, width, height);
    const points = this.selected().points || [];
    if (!points.length) {
      this.onFrame({ index: 0, progress: 0, point: null });
      return;
    }
    const xs = points.map((point) => point[0]);
    const ys = points.map((point) => point[1]);
    const minX = Math.min(...xs);
    const maxX = Math.max(...xs);
    const minY = Math.min(...ys);
    const maxY = Math.max(...ys);
    const padding = 24;
    const scaleX = (width - padding * 2) / Math.max(1e-9, maxX - minX);
    const scaleY = (height - padding * 2) / Math.max(1e-9, maxY - minY);
    const scale = Math.min(scaleX, scaleY);
    const project = (point) => [padding + (point[0] - minX) * scale, height - padding - (point[1] - minY) * scale];
    const visible = points.slice(0, this.frameIndex + 1);
    context.beginPath();
    visible.forEach((point, index) => {
      const [x, y] = project(point);
      if (index === 0) context.moveTo(x, y);
      else context.lineTo(x, y);
    });
    context.strokeStyle = "#0f766e";
    context.lineWidth = 2;
    context.stroke();
    const [currentX, currentY] = project(visible[visible.length - 1]);
    context.beginPath();
    context.arc(currentX, currentY, 5, 0, Math.PI * 2);
    context.fillStyle = "#d97706";
    context.fill();
    this.onFrame({
      index: this.frameIndex,
      progress: this.frameIndex / Math.max(1, points.length - 1),
      point: points[this.frameIndex],
    });
  }
}

