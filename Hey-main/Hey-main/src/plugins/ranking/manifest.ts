import { definePlugin } from '@plugins-core';

export const rankingPlugin = definePlugin({
    id: 'red-king.ranking',
    name: 'Ranking Dashboard',
    version: '1.0.0',
    description: 'Optional ranking and leaderboard capability for the Red King platform.',
    slot: 'plugin-dashboard',
    capabilities: ['ui', 'ranking'],
    menu: {
        label: 'Ranking',
        path: '/plugins/ranking',
        order: 90,
    },
});
