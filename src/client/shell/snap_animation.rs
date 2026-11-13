use super::*;
use crate::api::schema::PaneDirection;
use std::time::{Duration, Instant};

const DURATION: Duration = Duration::from_millis(160);
const FRAME_INTERVAL: Duration = Duration::from_millis(16);

#[derive(Clone, Debug)]
pub(super) struct SnapAnimation {
    started: Instant,
    running: bool,
    from: Option<Rect>,
}

impl SnapAnimation {
    pub(super) fn new() -> Self {
        Self {
            started: Instant::now(),
            running: true,
            from: None,
        }
    }

    pub(super) fn from_region(from: Rect) -> Self {
        Self {
            from: Some(from),
            ..Self::new()
        }
    }

    pub(super) fn region(&self, area: Rect, edge: PaneDirection, now: Instant) -> Rect {
        use PaneDirection::*;
        let t = (now.saturating_duration_since(self.started).as_secs_f32()
            / DURATION.as_secs_f32())
        .min(1.0);
        let fraction = 1.0 - (1.0 - t).powi(3);
        if let Some(from) = self.from {
            let lerp = |a: u16, b: u16| {
                (f32::from(a) + (f32::from(b) - f32::from(a)) * fraction).round() as u16
            };
            return Rect::new(
                lerp(from.x, area.x),
                lerp(from.y, area.y),
                lerp(from.width, area.width).max(1),
                lerp(from.height, area.height).max(1),
            );
        }
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
    fn snap_animation(&self) -> Option<&SnapAnimation> {
        match &self.chrome_drag {
            Some(ClientChromeDrag::Tab {
                snap: Some(snap), ..
            }) => Some(&snap.animation),
            Some(ClientChromeDrag::PaneToTab {
                stack_preview: Some(preview),
                ..
            }) => Some(&preview.animation),
            _ => None,
        }
    }

    pub(super) fn snap_preview_timer_delay(&self) -> Duration {
        if self.snap_animation().is_some_and(|a| a.running) {
            FRAME_INTERVAL
        } else {
            Duration::MAX
        }
    }

    pub(crate) fn tick_snap_preview(&mut self, now: Instant) -> bool {
        let animation = match &mut self.chrome_drag {
            Some(ClientChromeDrag::Tab {
                snap: Some(snap), ..
            }) => &mut snap.animation,
            Some(ClientChromeDrag::PaneToTab {
                stack_preview: Some(preview),
                ..
            }) => &mut preview.animation,
            _ => return false,
        };
        if !animation.running {
            return false;
        }
        animation.running = now.saturating_duration_since(animation.started) < DURATION;
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
            from: None,
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
