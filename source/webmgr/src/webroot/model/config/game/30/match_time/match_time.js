/**
 * @ author: wenshan @ date: 2015.3.24 @ from: index js
 * editby wangtao date: 2016.1.13
 */

// 显示比赛日程表

var match_times = [];
var matches = {};
var dates = {};

/*
从服务器获取数据
*/
function get_match_start_time_data(afterDataReady) {
    SS.getData(SS.url.model.t3card_get_match_time, {days: $("#days").val()},
    // SS.getData('/model/config/game/8/match_time/data1.json', {},
    function(da) {

        match_times = [];
        matches = [];
        dates = {};

        var _matches = {};

        for (var matchId in da.result.match_time) {
            var match_detail = da.result.match_time[matchId];

            _matches[matchId] = {
                matchId: matchId,
                name: match_detail.name,
                visible: match_detail.visible,
                istest: matchId.substr(0, 9) == 'mtt_test_' ? 1 : 0,
            }

            for (var roomId in match_detail.rooms) {
                for (var i in match_detail.rooms[roomId]) {

                    var time = match_detail.rooms[roomId][i]; // eg. "2016-01-25 12:00"
                    var date = time.split(' ')[0];  // eg. "2016-01-25"
                    dates[date] = 1;

                    var timepoint = {
                        name: match_detail.name,
                        roomId: roomId,
                        matchId: matchId,
                        time: time,
                        date: date,
                    };
                    match_times.push(timepoint);
                }
            }
        }

        for (var matchId in _matches) {
            matches.push(_matches[matchId]);
        }
        matches.sort(function(a, b) { return a.matchId <= b.matchId ? 1 : -1; });
        for (var i in matches) {
            console.log('i, match:', i, matches[i])
        }


        if (afterDataReady) {
            afterDataReady();
        }
    });
}

/*
刷新日期选择器
*/
function refresh_date_selector() {
    var data = [];
    for (var date in dates) {
        data.push({text: date});
    }
    $('#date_selector').datalist({
        data: data,
        singleSelect: false,
        checkOnSelect: true,
        selectOnCheck: true,
        toolbar: [
            {text: '全选', handler: function(){$('#date_selector').datalist('selectAll')}},
            {text: '全不选', handler: function(){$('#date_selector').datalist('unselectAll')}}
        ],
    });
    $('#date_selector').datalist('selectAll');
}

/*
刷新房间名选择器
*/
function refresh_match_selector() {
    var data = [];
    var selectedIds = [];
    for (var matchId in matches) {
        if (matches[matchId].visible && !matches[matchId].istest) {
            selectedIds.push(data.length);  // 要的是 index ，所以push length
        }
        data.push({
            name: matches[matchId].name,
            visible: matches[matchId].visible,
            istest: matches[matchId].istest,
        });
    }

    $('#match_selector').datagrid({
        data: data,
        checkbox: true,
        singleSelect: false,
        checkOnSelect: true,
        selectOnCheck: true,
        columns: [[
            {field: 'name', title: 'Name', width: 140},
            {field: 'visible', title: 'Visible', width: 50},
        ]],
        toolbar: [
            {text: '全选', handler: refresh_match_selector},
            {text: '真的全选', handler: function(){$('#match_selector').datalist('selectAll')}},
            {text: '全不选', handler: function(){$('#match_selector').datalist('unselectAll')}}
        ],
    });

    // 只选中需要选中的行
    for (var i in selectedIds) {
        var index = selectedIds[i];
        $('#match_selector').datalist('selectRow', index);
    }

}

/*
刷新主内容： 比赛时间列表
*/
function refresh_match_time() {
    var selectedMatch = {};
    var selectedDate = {};

    var allSelectedMatch = $('#match_selector').datalist('getSelections');
    var allSelectedDate = $('#date_selector').datalist('getSelections');

    for (var i in allSelectedMatch) {
        selectedMatch[allSelectedMatch[i].name] = 1;
    }
    for (var i in allSelectedDate) {
        selectedDate[allSelectedDate[i].text] = 1;
    }

    var data = [];
    for (var i in match_times) {
        if (selectedMatch[match_times[i].name] && selectedDate[match_times[i].date]) {
            data.push(match_times[i]);
        }
    }

    $('#match_time').datagrid({
        remoteSort: false,
        data: data,
        rownumbers: true,
        columns: [[
            {field: 'name', title: 'Room Name', width: 150, sortable: true},
            {field: 'time', title: 'Start Time', width: 150, sortable: true,
             sorter: function(a,b){return a==b?0: (a>b?1:-1);}
            },
            {field: 'roomId', title: 'Room Id', width: 50},

        ]],
    });
    $('#match_time').datagrid('sort', {
        sortName: 'time',
        sortOrder: 'asc'
    });
}

function refreshAll() {
    get_match_start_time_data(function () {
        refresh_match_selector();
        refresh_date_selector();
        refresh_match_time();
    });
}


$(function() {
    refreshAll();
});
