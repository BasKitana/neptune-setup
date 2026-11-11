use super::*;
use crate::api::schema::{Method, PaneDirection, TabSnapParams};
use ratatui::style::Color;

#[derive(Clone, Debug)]
pub(super) struct SnapTarget {
    pane_id: String,
    edge: PaneDirection,
    preview: Rect,
    pub(super) animation: super::snap_animation::SnapAnimation,
}

impl SnapTarget {
    pub(super) fn matches(&self, other: &Self) -> bool {
        self.pane_id == other.pane_id && self.edge == other.edge && self.preview == other.preview
    }

    pub(super) fn request(self, source_tab_id: String) -> Method {
        Method::TabSnap(TabSnapParams {
            source_tab_id,
            target_pane_id: self.pane_id,
            edge: self.edge,
        })
    }
}

impl ClientShellState {
    pub(super) fn tab_snap_enabled(&self) -> bool {
        self.active_endpoint_id == ClientEndpointId::Local
            && std::env::var_os("NEPTUNE_SNAP_PREVIEW").is_some_and(|value| value == "1")
    }

    pub(super) fn snap_target_at(
        &self,
        source_tab_id: &str,
        point: (u16, u16),
    ) -> Option<SnapTarget> {
        if !self.tab_snap_enabled()
            || self.overlay.is_some()
            || self.hits.popup.is_some()
            || self.pending_pane_surface.is_some()
        {
            return None;
        }
        let snapshot = self.snapshot.as_ref()?;
        let workspace_id = snapshot.focused_workspace_id.as_deref()?;
        let target_tab_id = snapshot.focused_tab_id.as_deref()?;
        if source_tab_id == target_tab_id
            || ![source_tab_id, target_tab_id].into_iter().all(|id| {
                snapshot
                    .tabs
                    .iter()
                    .any(|tab| tab.tab_id == id && tab.workspace_id == workspace_id && !tab.zoomed)
            })
        {
            return None;
        }
        let hit = self
            .hits
            .panes
            .iter()
            .find(|hit| contains(hit.rect, point))?;
        if !snapshot
            .panes
            .iter()
            .any(|pane| pane.pane_id == hit.pane_id && pane.tab_id == target_tab_id)
        {
            return None;
        }
        let (edge, preview) = snap_region(hit.rect, point)?;
        Some(SnapTarget {
            pane_id: hit.pane_id.clone(),
            edge,
            preview,
            animation: super::snap_animation::SnapAnimation::new(),
        })
    }

    pub(super) fn draw_snap_preview(&self, frame: &mut FrameData) {
        let Some(ClientChromeDrag::Tab {
            snap: Some(snap), ..
        }) = &self.chrome_drag
        else {
            return;
        };
        let preview = snap
            .animation
            .region(snap.preview, snap.edge, std::time::Instant::now());
        draw_outline(frame, preview, self.config.palette.accent);
    }
}

fn snap_region(area: Rect, point: (u16, u16)) -> Option<(PaneDirection, Rect)> {
    use PaneDirection::*;
    if !contains(area, point) {
        return None;
    }
    let (x, y) = point;
    let horizontal_band = (area.width / 4).clamp(2, 12);
    let vertical_band = (area.height / 4).clamp(1, 5);
    let (edge, _, _) = [
        (Left, x - area.x, horizontal_band),
        (Right, area.right() - x - 1, horizontal_band),
        (Up, y - area.y, vertical_band),
        (Down, area.bottom() - y - 1, vertical_band),
    ]
    .into_iter()
    .filter(|(edge, distance, band)| {
        distance < band
            && match edge {
                Left | Right => area.width >= 24 && area.height >= 4,
                Up | Down => area.height >= 8 && area.width >= 12,
            }
    })
    .min_by_key(|(_, distance, band)| u32::from(*distance) * 120 / u32::from(*band))?;
    let first_width = area.width.div_ceil(2);
    let first_height = area.height.div_ceil(2);
    let preview = match edge {
        Left => Rect::new(area.x, area.y, first_width, area.height),
        Right => Rect::new(
            area.x + first_width,
            area.y,
            area.width - first_width,
            area.height,
        ),
        Up => Rect::new(area.x, area.y, area.width, first_height),
        Down => Rect::new(
            area.x,
            area.y + first_height,
            area.width,
            area.height - first_height,
        ),
    };
    Some((edge, preview))
}

fn draw_outline(frame: &mut FrameData, area: Rect, accent: Color) {
    let mut cell = ratatui::buffer::Cell::default();
    cell.set_bg(accent);
    let bg = crate::protocol::CellData::from_ratatui_cell(&cell).bg;
    let width = usize::from(frame.width);
    let area = area.intersection(Rect::new(0, 0, frame.width, frame.height));
    if area.is_empty() {
        return;
    }
    for y in [area.y, area.bottom() - 1] {
        let start = usize::from(y) * width + usize::from(area.x);
        for cell in &mut frame.cells[start..start + usize::from(area.width)] {
            cell.bg = bg;
        }
    }
    for y in area.y + 1..area.bottom() - 1 {
        let start = usize::from(y) * width;
        frame.cells[start + usize::from(area.x)].bg = bg;
        frame.cells[start + usize::from(area.right() - 1)].bg = bg;
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn snap_regions_match_odd_split_dimensions_and_ignore_center() {
        let area = Rect::new(10, 2, 51, 21);
        assert_eq!(
            snap_region(area, (10, 12)),
            Some((PaneDirection::Left, Rect::new(10, 2, 26, 21)))
        );
        assert_eq!(
            snap_region(area, (60, 12)),
            Some((PaneDirection::Right, Rect::new(36, 2, 25, 21)))
        );
        assert_eq!(
            snap_region(area, (35, 2)),
            Some((PaneDirection::Up, Rect::new(10, 2, 51, 11)))
        );
        assert_eq!(
            snap_region(area, (35, 22)),
            Some((PaneDirection::Down, Rect::new(10, 13, 51, 10)))
        );
        assert!(snap_region(area, (35, 12)).is_none());
        assert!(snap_region(Rect::new(0, 0, 8, 5), (0, 0)).is_none());
    }
}

impl ClientShellState {
    fn detachable_pane(&self, pane_id: &str) -> Option<&crate::protocol::ClientShellPane> {
        if !self.tab_snap_enabled() || self.overlay.is_some() || self.hits.popup.is_some() {
            return None;
        }
        let snapshot = self.snapshot.as_ref()?;
        let pane = snapshot.panes.iter().find(|pane| pane.pane_id == pane_id)?;
        if snapshot.focused_workspace_id.as_deref() != Some(&pane.workspace_id)
            || !snapshot
                .tabs
                .iter()
                .any(|tab| tab.tab_id == pane.tab_id && !tab.zoomed)
            || !snapshot
                .panes
                .iter()
                .any(|other| other.tab_id == pane.tab_id && other.pane_id != pane_id)
        {
            return None;
        }
        Some(pane)
    }

    pub(super) fn start_pane_to_tab(&mut self, pane_id: String, point: (u16, u16)) -> bool {
        if self.detachable_pane(&pane_id).is_none() {
            return false;
        }
        self.chrome_drag = Some(ClientChromeDrag::PaneToTab {
            pane_id,
            start: point,
            dragging: false,
            over_tab_bar: false,
        });
        true
    }

    pub(super) fn pane_to_tab_drop_at(&self, point: (u16, u16)) -> bool {
        contains(self.hits.new_tab, point) || self.tab_drop_index_at(point).is_some()
    }

    pub(super) fn finish_pane_to_tab(
        &mut self,
        pane_id: String,
        dragging: bool,
        point: (u16, u16),
        outcome: &mut ClientShellInput,
    ) {
        use crate::api::schema::{PaneMoveDestination, PaneMoveParams, PaneTarget};
        if !dragging {
            self.push_endpoint_method(Method::PaneFocus(PaneTarget { pane_id }), outcome);
        } else if self.pane_to_tab_drop_at(point) {
            if let Some(pane) = self.detachable_pane(&pane_id) {
                let destination = PaneMoveDestination::NewTab {
                    workspace_id: Some(pane.workspace_id.clone()),
                    label: pane.label.clone(),
                };
                self.push_endpoint_method(
                    Method::PaneMove(PaneMoveParams {
                        pane_id,
                        destination,
                        focus: true,
                    }),
                    outcome,
                );
            }
        }
        outcome.repaint = true;
    }
}
