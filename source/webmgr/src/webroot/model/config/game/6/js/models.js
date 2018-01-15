
function RoomModel(roomId) {
	// 房间ID
	this.roomId = roomId;
	// 房间类型
	this.typeName = null;
	
	this.name = '';
	this.playMode = 'happy:1';
	
	// 带入金币
	this.buyinChip = 0;
	this.minCoin = 0;
	this.minCoinQS = 0;		
	this.maxCoin = 0;
	this.maxCoinQS = 0;

	this.roomFee = 0;
	this.roomMutil = 0;
	this.roomLevel = 0;
	this.sendCoupon = 0;
	this.showCard = 0;
	this.winDesc = '';
	
	this.goodCard = 0;
	
	this.hasRobot = 0;
	
	this.robotCallUpTime = 0;
	this.robotMaxCount = 0;
	this.robotOpTimeMin = 1;
	this.robotOpTimeMax = 2;

	// 桌子配置
	// 是否能聊天
	this.canChat = 0;
	// 牌桌记牌器价格
	this.cardNoteChip = 0;
	// 大满贯倍数	
	this.gslam = 128;
	// 好牌概率
	this.lucky = 0;
	// 操作超时
	this.opTime = 15;
	// 管不住牌时的超时
	this.passTime = 5;
	// 二斗玩法的让牌倍数类型是1，2，其它玩法1
	this.rangPaiMultiType = 1;
	// 
	this.robotTimes = 1;
	// 防作弊
	this.unticheat = 0;
	// 比赛配置
	this.matchModel = null;
}

var playModes = [
	{
		'name':'欢乐',
		'value':'happy:1',
		'playMode':'happy',
		'grab':1
	},
	{
		'name':'经典',
		'value':'123:0',
		'playMode':'123',
		'grab':0
	},
	{
		'name':'二斗',
		'value':'erdou:1',
		'playMode':'erdou',
		'grab':1
	},
	{
		'name':'癞子',
		'value':'wild:1',
		'playMode':'wild',
		'grab':1
	}
];

function checkPlayMode(obj) {
	playMode = obj['playMode'] + ':' + obj['tableConf']['grab'];
	for (var i = 0; i < playModes.length; i++) {
		if (playMode == playModes[i].value) {
			return playMode;
		}
	}
	throw new Error('Bad playMode and grab: ' + playMode);
}

var roomTypeValueNameMap = {
	'normal':'普通',
	'group_match':'分组赛',
	'arena_match':'Arena'
}

function indexOfPlayMode(playMode) {
	for (var i = 0; i < playModes.length; i++) {
		if (playModes[i]['value'] == playMode) {
			return i;
		}		
	}
	return -1;
}

function isValidPlayModeAndGrab(obj) {
	playMode = obj['playMode'];
	grab = obj['tableConf']['grab'];
	return indexOfPlayMode(playMode + ':' + grab) != -1;
}

RoomModel.decode = function(roomId, obj) {
	console.log('RoomModel.decode', roomId, obj);
	if (!isInt(roomId)) {
		throw new Error('roomId must be int');
	}
	var ret = new RoomModel(roomId);
	if (!isValidPlayModeAndGrab(obj)) {
		throw new Error('Bad playMode and garb: '
						+ obj['playMode']
						+ ':'
						+ obj['tableConf']['grab']);
	}
	ret.typeName = checkString(obj, 'typeName');
	ret.buyinChip = checkInt(obj, 'buyinchip');
	ret.goodCard = checkBoolInt(obj, 'goodCard');
	ret.hasRobot = checkBoolInt(obj, 'hasrobot');
	ret.minCoin = checkInt(obj, 'minCoin');
	ret.minCoinQS = checkInt(obj, 'minCoinQS');
	ret.maxCoin = checkInt(obj, 'buyinchip');
	ret.maxCoinQS = checkInt(obj, 'maxCoinQS');
	ret.name = checkString(obj, 'name');
	ret.playMode = checkPlayMode(obj);
	ret.roomFee = checkInt(obj, 'roomFee');
	ret.roomMutil = checkInt(obj, 'roomMutil');
	ret.roomLevel = checkIntDefault(obj, 'roomLevel', 0);
	ret.sendCoupon = checkBoolInt(obj, 'sendCoupon');
	ret.showCard = checkBoolInt(obj, 'showCard');
	ret.winDesc = checkString(obj, 'winDesc');

	ret.robotCallUpTime = checkInt(obj, 'robotUserCallUpTime');
	ret.robotMaxCount = checkInt(obj, 'robotUserMaxCount');
	robotOpTime = checkIntArray(obj, 'robotUserOpTime');
	if (robotOpTime.length != 2) {
		throw new Error('Field robotUserOpTime must be int array with length=2: ' + robotOpTime);
	}
	ret.robotOpTimeMin = robotOpTime[0];
	ret.robotOpTimeMax = robotOpTime[1];
	
	matchConf = obj['matchConf'];
	
	if (matchConf) {
		
	}
	return ret;
}

RoomModel.prototype.toJson = function() {
	var ret = {};
	ret['typeName'] = this.typeName;
	ret['buyinchip'] = this.buyinChip;
	ret['dummyUserCount'] = 0;
	ret['goodCard'] = this.goodCard;
	ret['hasrobot'] = this.hasRobot;
	ret['minCoin'] = this.minCoin;
	ret['minCoinQS'] = this.minCoinQS;
	ret['maxCoin'] = this.maxCoin;
	ret['maxCoinQS'] = this.maxCoinQS;
	ret['name'] = this.name;
	ret['playMode'] = playModes[this.playMode]['playMode'];
	ret['roomFee'] = this.roomFee;
	ret['roomMutil'] = this.roomMutil;
	ret['roomLevel'] = this.roomLevel;
	ret['sendCoupon'] = this.sendCoupon;
	ret['showCard'] = this.showCard;
	ret['winDesc'] = this.winDesc;
	
	tableConf = {};
	tableConf['autochange'] = 1;
	tableConf['basebet'] = 1;
	tableConf['basemulti'] = 1;
	tableConf['cardNoteChip'] = this.cardNotChip;
	tableConf['canchat'] = this.canChat;
	tableConf['coin2chip'] = 1;
	tableConf['grab'] = playModes[this.playMode]['grab'];
	tableConf['luck'] = this.luck;
	tableConf['maxSeatN'] = this.playMode == 'erdou' ? 2 : 3;
	tableConf['optime'] = this.opTime;
	tableConf['passtime'] = this.passTime;
	tableConf['rangPaiMultiType'] = this.rangPaiMultiType;
	tableConf['robottimes'] = this.robotTimes;
	tableConf['unticheat'] = this.unticheat;
	ret['tableConf'] = tableConf;
	
	if (this.matchConf) {
		ret['ismatch'] = 1;
		ret['matchConf'] = this.matchModel.toJson();
	} else {
		ret['ismatch'] = 0;
	}
	return ret;
}

function GroupMatchModel() {
}

function ArenaMatchModel() {
}

