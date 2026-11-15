$(function()
{
    var dashboard = $('.achi-dashboard');
    var activeFilter = 'all';
    var showPrevious = false;

    function applyAchievementFilters()
    {
        var query = $.trim(dashboard.find('.achi-search__input').val() || '').toLowerCase();
        var visibleCount = 0;

        dashboard.find('.achi-entry').each(function()
        {
            var entry = $(this);
            var state = entry.attr('data-achievement-state');
            var matchesFilter = activeFilter === 'all'
                ? (state !== 'previous' || showPrevious)
                : (activeFilter === 'previous' ? state === 'previous' : (activeFilter === 'locked' ? state === 'locked' : state === 'current'));
            var matchesSearch = !query || entry.text().toLowerCase().indexOf(query) !== -1;
            var visible = matchesFilter && matchesSearch;

            entry.toggleClass('is-filtered-out', !visible);
            entry.toggle(visible);

            if (visible)
            {
                visibleCount++;
            }
        });

        dashboard.find('.achi-no-results').prop('hidden', visibleCount !== 0);
    }

    dashboard.find('.achi-filter').on('click', function()
    {
        var button = $(this);
        activeFilter = button.attr('data-filter');

        dashboard.find('.achi-filter')
            .removeClass('is-active')
            .attr('aria-pressed', 'false');
        button.addClass('is-active').attr('aria-pressed', 'true');

        if (activeFilter === 'previous')
        {
            showPrevious = true;
            dashboard.find('.achi-previous-toggle')
                .text('Hide previous levels')
                .attr('aria-expanded', 'true');
        }

        applyAchievementFilters();
    });

    dashboard.find('.achi-search__input').on('input', applyAchievementFilters);

    dashboard.find('.achi-previous-toggle').on('click', function(e)
    {
        e.preventDefault();
        showPrevious = !showPrevious;

        var link = $(this);
        link.text(showPrevious ? 'Hide previous levels' : 'Show previous levels');
        link.attr('aria-expanded', showPrevious ? 'true' : 'false');

        if (activeFilter === 'previous' && !showPrevious)
        {
            activeFilter = 'all';
            dashboard.find('.achi-filter')
                .removeClass('is-active')
                .attr('aria-pressed', 'false');
            dashboard.find('.achi-filter[data-filter="all"]')
                .addClass('is-active')
                .attr('aria-pressed', 'true');
        }

        applyAchievementFilters();
    });

    dashboard.on('click', '.entries-trigger, .entries-trigger-button', function(e)
    {
        var target = $(this).closest('.achi-entry').find('.entries-wrapper');
        toggleEntries(target, [], false);
        e.preventDefault();
    });


    applyAchievementFilters();
});
