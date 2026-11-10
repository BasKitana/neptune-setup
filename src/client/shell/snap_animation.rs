use super::*;
use crate::api::schema::PaneDirection;
use std::time::{Duration, Instant};

const DURATION: Duration = Duration::from_millis(140);
const FRAME_INTERVAL: Duration = Duration::from_millis(16);

#[derive(Clone, Debug)]
pub(super) struct SnapAnimation {
    started: Instant,
    running: bool,
}

impl SnapAnimation {
    pub(super) fn new() -> Self {
        Self {
            started: Instant::now(),
            running: true,
        }
    }

    pub(super) fn region(&self, area: Rect, edge: PaneDirection, now: Instant) -> Rect {
        use PaneDirection::*;
        let t = (now.saturating_duration_since(self.started).as_secs_f32()
            / DURATION.as_secs_f32())
        .min(1.0);
        let fraction = 1.0 - (1.0 - t).powi(3);
        let extent = |length: u16| (f32::from(length) * fraction).round().max(1.0) as u16;
        match edge {
            Left => Rect::new(area.x, area.y, extent(area.width), area.height),
            Right => {
                let width = extent(area.width);
                Rect::new(area.right() - width, area.y, width, area.height)
            }
            Up => Rect::new(area.x, area.y, area.width, extent(area.height)),
            Down => {
                let height = extent(area.height);
                Rect::new(area.x, area.bottom() - height, area.width, height)
            }
        }
    }
}

impl ClientShellState {
    pub(super) fn snap_preview_timer_delay(&self) -> Duration {
        if matches!(&self.chrome_drag, Some(ClientChromeDrag::Tab { snap: Some(snap), .. }) if snap.animation.running)
        {
            FRAME_INTERVAL
        } else {
            Duration::MAX
        }
    }

    pub(crate) fn tick_snap_preview(&mut self, now: Instant) -> bool {
        let Some(ClientChromeDrag::Tab {
            snap: Some(snap), ..
        }) = &mut self.chrome_drag
        else {
            return false;
        };
        if !snap.animation.running {
            return false;
        }
        snap.animation.running = now.saturating_duration_since(snap.animation.started) < DURATION;
        true
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn preview_grows_from_each_edge_and_ends_on_the_exact_drop_region() {
        let started = Instant::now();
        let animation = SnapAnimation {
            started,
            running: true,
        };
        let area = Rect::new(10, 4, 40, 24);
        for (edge, initial) in [
            (PaneDirection::Left, Rect::new(10, 4, 1, 24)),
            (PaneDirection::Right, Rect::new(49, 4, 1, 24)),
            (PaneDirection::Up, Rect::new(10, 4, 40, 1)),
            (PaneDirection::Down, Rect::new(10, 27, 40, 1)),
        ] {
            assert_eq!(animation.region(area, edge, started), initial);
            let middle = animation.region(area, edge, started + DURATION / 2);
            assert!(middle.area() > initial.area());
            assert!(middle.area() < area.area());
            assert_eq!(animation.region(area, edge, started + DURATION), area);
        }
    }
}
