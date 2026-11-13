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

#[derive(Clone, Debug)]
pub(super) struct PaneDropPreview {
    target: String,
    edge: Option<PaneDirection>,
    rect: Rect,
    pub(super) animation: super::snap_animation::SnapAnimation,
}

impl ClientShellState {
    pub(super) fn add_terminal_tab(
        &mut self,
        target_pane_id: Option<String>,
        outcome: &mut ClientShellInput,
    ) {
        use crate::api::schema::{PaneSplitParams, SplitDirection};
        if target_pane_id.is_some() {
            self.push_endpoint_method(
                Method::PaneSplit(PaneSplitParams {
                    stack: true,
                    target_pane_id,
                    workspace_id: None,
                    direction: SplitDirection::Right,
                    ratio: None,
                    cwd: None,
                    focus: true,
                    right_click: Default::default(),
                    env: Default::default(),
                }),
                outcome,
            );
        }
    }
}

impl PaneDropPreview {
    pub(super) fn matches(&self, other: &Self) -> bool {
        self.target == other.target && self.edge == other.edge && self.rect == other.rect
    }

    fn region(&self, now: std::time::Instant) -> Rect {
        self.animation
            .region(self.rect, self.edge.unwrap_or(PaneDirection::Down), now)
    }

    pub(super) fn transition_from(&mut self, old: &Self) {
        self.animation = super::snap_animation::SnapAnimation::from_region(
            old.region(std::time::Instant::now()),
        );
    }
}

impl SnapTarget {
    pub(super) fn matches(&self, other: &Self) -> bool {
        self.pane_id == other.pane_id && self.edge == other.edge && self.preview == other.preview
    }

    pub(super) fn transition_from(&mut self, old: &Self) {
        self.animation = super::snap_animation::SnapAnimation::from_region(old.animation.region(
            old.preview,
            old.edge,
            std::time::Instant::now(),
        ));
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
        if let Some(ClientChromeDrag::PaneToTab {
            stack_preview: Some(preview),
            ..
        }) = &self.chrome_drag
        {
            draw_drop_preview(
                frame,
                preview.region(std::time::Instant::now()),
                &self.config.palette,
                if preview.edge.is_some() {
                    " Split "
                } else {
                    " Join tabs "
                },
            );
            return;
        }
        let Some(ClientChromeDrag::Tab {
            snap: Some(snap), ..
        }) = &self.chrome_drag
        else {
            return;
        };
        let preview = snap
            .animation
            .region(snap.preview, snap.edge, std::time::Instant::now());
        draw_drop_preview(frame, preview, &self.config.palette, " Split ");
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

fn draw_drop_preview(frame: &mut FrameData, area: Rect, palette: &Palette, label: &str) {
    let area = area.intersection(Rect::new(0, 0, frame.width, frame.height));
    if area.is_empty() {
        return;
    }
    let Color::Rgb(r, g, b) = palette.accent else {
        return;
    };
    let tint = |base: u32| {
        let base = if base >> 24 == 2 { base } else { 0x020f141e };
        let blend =
            |shift: u32, accent: u8| (((base >> shift) & 255u32) * 4 + u32::from(accent)) / 5;
        0x02000000 | (blend(16, r) << 16) | (blend(8, g) << 8) | blend(0, b)
    };
    let width = usize::from(frame.width);
    for y in area.y..area.bottom() {
        for x in area.x..area.right() {
            let cell = &mut frame.cells[usize::from(y) * width + usize::from(x)];
            cell.bg = tint(cell.bg);
        }
    }
    let mut buffer = Buffer::empty(area);
    let style = Style::default()
        .fg(palette.accent)
        .bg(Color::Rgb(r / 5, g / 5, b / 5));
    use ratatui::widgets::{Block, BorderType, Borders, Widget};
    Block::default()
        .borders(Borders::ALL)
        .border_type(BorderType::Rounded)
        .border_style(style)
        .render(area, &mut buffer);
    for y in area.y..area.bottom() {
        for x in area.x..area.right() {
            if x == area.x || x + 1 == area.right() || y == area.y || y + 1 == area.bottom() {
                frame.cells[usize::from(y) * width + usize::from(x)] =
                    crate::protocol::CellData::from_ratatui_cell(&buffer[(x, y)]);
            }
        }
    }
    if area.width >= label.len() as u16 + 2 && area.height >= 3 {
        let text = Rect::new(
            area.x + (area.width - label.len() as u16) / 2,
            area.y + area.height / 2,
            label.len() as u16,
            1,
        );
        let mut buffer = Buffer::empty(text);
        render::put_text(
            &mut buffer,
            text.x,
            text.y,
            text.width,
            label,
            Style::default().fg(palette.panel_bg).bg(palette.accent),
        );
        for x in text.x..text.right() {
            frame.cells[usize::from(text.y) * width + usize::from(x)] =
                crate::protocol::CellData::from_ratatui_cell(&buffer[(x, text.y)]);
        }
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
            stack_preview: None,
        });
        true
    }

    pub(super) fn pane_to_tab_drop_at(&self, point: (u16, u16)) -> bool {
        !self
            .hits
            .stack_tabs
            .iter()
            .any(|(rect, _)| contains(*rect, point))
            && (contains(self.hits.new_tab, point) || self.tab_drop_index_at(point).is_some())
    }

    pub(super) fn pane_drop_preview_at(
        &self,
        source: &str,
        point: (u16, u16),
    ) -> Option<PaneDropPreview> {
        let pane = self.detachable_pane(source)?;
        let snapshot = self.snapshot.as_ref()?;
        if snapshot.focused_tab_id.as_deref() != Some(&pane.tab_id)
            || self.pending_pane_surface.is_some()
        {
            return None;
        }
        let header_member = self
            .hits
            .stack_tabs
            .iter()
            .find(|(rect, _)| contains(*rect, point))
            .map(|(_, id)| id);
        let hit = self.hits.panes.iter().find(|hit| {
            contains(hit.rect, point)
                || header_member.is_some_and(|id| {
                    id == &hit.pane_id
                        || snapshot
                            .pane_stacks
                            .get(&hit.pane_id)
                            .is_some_and(|members| members.contains(id))
                })
        })?;
        let members = snapshot.pane_stacks.get(&hit.pane_id);
        let same_group =
            hit.pane_id == source || members.is_some_and(|ids| ids.iter().any(|id| id == source));
        let header =
            header_member.is_some() || (point.1 == hit.rect.y && hit.inner_rect.y > hit.rect.y);
        let split = if header {
            None
        } else {
            snap_region(hit.rect, point)
        };
        if same_group && (split.is_none() || members.is_none_or(|ids| ids.len() < 2)) {
            return None;
        }
        let target = if hit.pane_id == source {
            members?.iter().find(|id| id.as_str() != source)?.clone()
        } else {
            hit.pane_id.clone()
        };
        let (edge, rect) = split.map_or((None, hit.rect), |(edge, rect)| (Some(edge), rect));
        Some(PaneDropPreview {
            target,
            edge,
            rect,
            animation: super::snap_animation::SnapAnimation::new(),
        })
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
        } else if let Some(preview) = self.pane_drop_preview_at(&pane_id, point) {
            let method = if let Some(edge) = preview.edge {
                Method::PaneDock(crate::api::schema::PaneDockParams {
                    source_pane_id: pane_id,
                    target_pane_id: preview.target,
                    edge,
                })
            } else {
                Method::PaneStack(crate::api::schema::PaneStackParams {
                    source_pane_id: pane_id,
                    target_pane_id: preview.target,
                })
            };
            self.push_endpoint_method(method, outcome);
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

pub(super) fn pane_tab_label(
    snapshot: &ClientShellSnapshot,
    id: &str,
    multiple: bool,
    branches_differ: bool,
) -> String {
    use crate::api::schema::AgentStatus;
    let activity = snapshot.pane_activity.get(id);
    let agent = snapshot.agents.iter().find(|agent| agent.pane_id == id);
    let number = snapshot.terminal_numbers.get(id).copied();
    let mut label = if let Some(agent) = agent {
        let name = agent
            .display_agent
            .as_deref()
            .or(agent.agent.as_deref())
            .unwrap_or("Agent");
        let name = if name.eq_ignore_ascii_case("codex") {
            "Codex"
        } else {
            name
        };
        let title = agent
            .title
            .as_deref()
            .or(agent.terminal_title_stripped.as_deref())
            .map(str::trim)
            .filter(|title| {
                !title.is_empty()
                    && !title.eq_ignore_ascii_case(name)
                    && !snapshot
                        .panes
                        .iter()
                        .find(|pane| pane.pane_id == id)
                        .is_some_and(|pane| {
                            [pane.cwd.as_deref(), pane.foreground_cwd.as_deref()]
                                .into_iter()
                                .flatten()
                                .filter_map(|cwd| {
                                    cwd.trim_end_matches(['/', '\\']).rsplit(['/', '\\']).next()
                                })
                                .any(|folder| title.eq_ignore_ascii_case(folder))
                        })
                    && !title
                        .split_once(':')
                        .is_some_and(|(prefix, _)| prefix.contains('@'))
                    && !title.contains(":/")
                    && !title.contains(": ~")
                    && !title.starts_with('/')
                    && !title.starts_with('~')
            });
        let state = match agent.agent_status {
            AgentStatus::Working => Some("working"),
            AgentStatus::Blocked => Some("waiting"),
            AgentStatus::Idle => Some("idle"),
            AgentStatus::Done => Some("done"),
            AgentStatus::Unknown => None,
        };
        let title = title.unwrap_or(name);
        state.map_or_else(|| title.to_owned(), |state| format!("{title} · {state}"))
    } else if let Some(label) =
        activity.and_then(|activity| activity.running.as_ref().or(activity.last_result.as_ref()))
    {
        label.clone()
    } else {
        match number {
            Some(number) if multiple || snapshot.numbered_panes || number > 1 => {
                format!("Terminal {number}")
            }
            _ => "Terminal".into(),
        }
    };
    if branches_differ {
        if let Some(branch) = activity.and_then(|activity| activity.branch.as_deref()) {
            label.push_str(" · ");
            label.push_str(branch);
        }
    }
    label
}

pub(super) fn draw_stack_tabs(
    frame: &mut FrameData,
    snapshot: &ClientShellSnapshot,
    panes: &[PaneHit],
    palette: &Palette,
    tab_strip: Rect,
    close: &mut Vec<(Rect, String)>,
) -> (Vec<(Rect, String)>, Vec<(Rect, String)>) {
    let mut add = Vec::new();
    let mut hits = Vec::new();
    let top = panes.iter().map(|p| p.rect.y).min().unwrap_or(0);
    let branches_differ = {
        let mut branches = snapshot
            .pane_activity
            .values()
            .filter_map(|activity| activity.branch.as_deref());
        branches
            .next()
            .is_some_and(|first| branches.any(|branch| branch != first))
    };
    let multiple_panes = snapshot
        .panes
        .iter()
        .filter(|pane| Some(pane.workspace_id.as_str()) == snapshot.focused_workspace_id.as_deref())
        .take(2)
        .count()
        > 1;
    for pane in panes {
        let members = snapshot
            .pane_stacks
            .get(&pane.pane_id)
            .map(Vec::as_slice)
            .unwrap_or_else(|| std::slice::from_ref(&pane.pane_id));
        let tab_strip = Rect::new(
            pane.rect.x,
            if pane.rect.y == top {
                tab_strip.y
            } else {
                pane.rect.y
            },
            pane.rect.width,
            1,
        );
        let strip_x = tab_strip.x;
        let tab_cap =
            (tab_strip.width.saturating_sub(2) as usize / members.len().max(1)).min(44) as u16;
        let available = tab_strip.width.saturating_sub(2);
        let count = members.len().min(usize::from(available));
        if count == 0 || tab_strip.is_empty() || tab_strip.y >= frame.height {
            continue;
        }
        let mut x = strip_x;
        for member in members.iter().take(count) {
            let cap = tab_cap.min(tab_strip.right().saturating_sub(x));
            if cap == 0 {
                break;
            }
            let label = pane_tab_label(snapshot, member, multiple_panes, branches_differ);
            let width = render::display_width(&label)
                .saturating_add(4)
                .clamp(8, 44)
                .min(cap.saturating_sub(1).max(1));
            let area = Rect::new(x, tab_strip.y, width, 1);
            let mut buffer = Buffer::empty(area);
            let style = if member == &pane.pane_id {
                Style::default().fg(palette.accent).bg(palette.surface0)
            } else {
                Style::default().fg(palette.text).bg(palette.surface0)
            };
            buffer.set_style(area, style);
            render::put_text(
                &mut buffer,
                area.x,
                area.y,
                if width >= 4 { width - 2 } else { width },
                &format!(" {label} "),
                style,
            );
            if width >= 4 {
                let button = Rect::new(area.right() - 2, area.y, 2, 1);
                render::put_text(
                    &mut buffer,
                    button.x,
                    button.y,
                    button.width,
                    "\u{00d7}",
                    style,
                );
                close.push((button, member.clone()));
            }
            let offset = usize::from(area.y) * usize::from(frame.width);
            for col in area.x..area.right().min(frame.width) {
                frame.cells[offset + usize::from(col)] =
                    crate::protocol::CellData::from_ratatui_cell(&buffer[(col, area.y)]);
            }
            hits.push((area, member.clone()));
            x += width + u16::from(cap > width);
        }
        if x < tab_strip.right().min(frame.width) {
            let area = Rect::new(x, tab_strip.y, 1, 1);
            let mut buffer = Buffer::empty(area);
            render::put_text(
                &mut buffer,
                x,
                area.y,
                1,
                "+",
                Style::default().fg(palette.text),
            );
            frame.cells[usize::from(area.y) * usize::from(frame.width) + usize::from(x)] =
                crate::protocol::CellData::from_ratatui_cell(&buffer[(x, area.y)]);
            add.push((area, pane.pane_id.clone()));
        }
    }
    (hits, add)
}
