
var boolNameValues = [
	{'name':'是', 'value':1},
	{'name':'否', 'value':0}
];

var rangpaiMutilTypeNameValues = [
	{'name':'+1', 'value':1},
	{'name':'*2', 'value':2}
];

function RoomModelView(node, model) {
	this.rootNode = node;
	this.model = model;
	this._controls = [];
}

RoomModelView.prototype.getElementByName = function(name) {
	selector = '[name="' + name + '"]';
	return this.rootNode.querySelector(selector);
}

RoomModelView.createView = function(node, model) {
	if (model.typeName === 'normal') {
		return new NormalRoomModelView(node, model);
	} else if (model.typeName === 'arena_match') {
		return new ArenaMatchRoomModelView(node, model);
	} else if (model.typeName === 'group_match') {
		return new GroupMatchRoomModelView(node, model);
	}
	return null;
}

RoomModelView.prototype.initView = function() {
	console.log('>>> RoomModelView.prototype.initView');
	this.roomId = new InputControl(this.getElementByName('roomId'), '');
	this.typeName = new InputControl(this.getElementByName('typeName'), '');
	this.roomName = new NotEmptyInputControl(this.getElementByName('roomName'), '请输入房间名称');
	this.playMode = new SelectControl(this.getElementByName('playMode'), '请选择玩法', playModes);

	this._initViewImpl();
	
	this.updateView();
	
	console.log('<<< RoomModelView.prototype.initView');
}

RoomModelView.prototype.updateView = function() {
	console.log('>>> RoomModelView.prototype.updateView');
	
	this.roomId.setValue(this.model.roomId);
	this.typeName.setValue(roomTypeValueNameMap[this.model.typeName]);
	this.roomName.setValue(this.model.name);
	this.playMode.setValue(this.model.playMode);
	
	this._updateViewImpl();
	
	console.log('<<< RoomModelView.prototype.updateView');
}

RoomModelView.prototype.updateModel = function() {
	console.log('>>> RoomModelView.prototype.updateModel');
	this.checkValid();
	this._updateModelImpl();
	console.log('<<< RoomModelView.prototype.updateModel');
}

RoomModelView.prototype.checkValid = function() {
	console.log('>>> RoomModelView.prototype.checkValid');
	try {
		this.roomName.checkValid();
		this._checkValidImpl();
	} catch(e) {
		console.log(e);
		if (e instanceof InvalidateDataException) {
			alert(e.message);
			e.control.element.focus();
		}
	}
	console.log('<<< RoomModelView.prototype.checkValid');
}

RoomModelView.prototype._initViewImpl = function() {
}

RoomModelView.prototype._updateViewImpl = function() {
}

RoomModelView.prototype._checkValidImpl = function() {
}

RoomModelView.prototype._updateModelImpl = function() {
}

function NormalRoomModelView(node, model) {
	RoomModelView.call(this, node, model);
}

inheritPrototype(NormalRoomModelView, RoomModelView);

NormalRoomModelView.prototype._initViewImpl = function() {
	console.log('>>> NormalRoomModelView.prototype._initViewImpl');

	this.buyinChip = new NumberInputControl(this.getElementByName('buyinChip'), '带入必须是整数');
	this.minCoin = new NumberInputControl(this.getElementByName('minCoin'), '准入必须是整数');
	this.maxCoin = new NumberInputControl(this.getElementByName('maxCoin'), '准入必须是整数');
	this.minCoinQS = new NumberInputControl(this.getElementByName('minCoinQS'), '快开必须是整数');
	this.maxCoinQS = new NumberInputControl(this.getElementByName('maxCoinQS'), '快开必须是整数');
	this.roomFee = new NumberInputControl(this.getElementByName('roomFee'), '服务费必须是整数');
	this.roomMutil = new NumberInputControl(this.getElementByName('roomMutil'), '底注必须是整数');
	this.roomLevel = new NumberInputControl(this.getElementByName('roomLevel'), '房间级别必须是整数');
	this.winDesc = new InputControl(this.getElementByName('winDesc'), '');
	
	this.sendCoupon = new SelectControl(this.getElementByName('sendCoupon'), '请选择是否送券', boolNameValues);
	this.showCard = new SelectControl(this.getElementByName('showCard'), '请选择是否明牌', boolNameValues);
	this.goodCard = new SelectControl(this.getElementByName('goodCard'), '请选择是否有好牌', boolNameValues);
	this.lucky = new LimitNumberInputControl(this.getElementByName('lucky'), '请选择是否送', 0, 100);
	this.canChat = new SelectControl(this.getElementByName('canChat'), '请选择是否送券', boolNameValues);
	this.unticheat = new SelectControl(this.getElementByName('unticheat'), '请选择是否送券', boolNameValues);
	
	this.gslam = new NumberInputControl(this.getElementByName('gslam'), '大满贯倍数必须是整数');
	this.cardNoteChip = new NumberInputControl(this.getElementByName('cardNoteChip'), '牌局记牌器价格必须是整数');
	
	this.opTime = new NumberInputControl(this.getElementByName('opTime'), '操作超时必须是整数');
	this.robotTimes = new NumberInputControl(this.getElementByName('robotTimes'), '托管超时次数必须是整数');
	this.passTime = new NumberInputControl(this.getElementByName('passTime'), '过牌超时必须是整数');
	
	this.rangPaiMultiType = new SelectControl(this.getElementByName('rangPaiMultiType'), '请选择二斗让牌倍数类型', rangpaiMutilTypeNameValues);
	this.hasRobot = new SelectControl(this.getElementByName('hasRobot'), '请选择是否有机器人', boolNameValues);
	
	this.robotCallUpTime = new NumberInputControl(this.getElementByName('robotCallUpTime'), '机器人唤醒时间必须是整数');
	this.robotMaxCount = new NumberInputControl(this.getElementByName('robotMaxCount'), '机器人数量必须是整数');
	this.robotOpTimeMin = new NumberInputControl(this.getElementByName('robotOpTimeMin'), '机器人操作时间必须是整数');
	this.robotOpTimeMax = new NumberInputControl(this.getElementByName('robotOpTimeMax'), '机器人操作时间必须是整数');
	
	console.log('<<< NormalRoomModelView.prototype._initViewImpl');
}

NormalRoomModelView.prototype._updateViewImpl = function() {
	console.log('>>> NormalRoomModelView.prototype._updateViewImpl');
	
	this.buyinChip.setValue(this.model.buyinChip);
	this.minCoin.setValue(this.model.minCoin);
	this.maxCoin.setValue(this.model.maxCoin);
	this.minCoinQS.setValue(this.model.minCoinQS);
	this.maxCoinQS.setValue(this.model.maxCoinQS);
	this.roomFee.setValue(this.model.roomFee);
	this.roomMutil.setValue(this.model.roomMutil);
	this.roomLevel.setValue(this.model.roomLevel);
	this.winDesc.setValue(this.model.winDesc);
	
	this.sendCoupon.setValue(this.model.sendCoupon);
	this.showCard.setValue(this.model.showCard);
	this.goodCard.setValue(this.model.goodCard);
	this.lucky.setValue(this.model.lucky);
	this.canChat.setValue(this.model.canChat);
	this.unticheat.setValue(this.model.unticheat);
	this.gslam.setValue(this.model.gslam);
	this.cardNoteChip.setValue(this.model.cardNoteChip);
	
	this.opTime.setValue(this.model.opTime);
	this.robotTimes.setValue(this.model.robotTimes);
	this.passTime.setValue(this.model.passTime);
	
	this.rangPaiMultiType.setValue(this.model.rangPaiMultiType);
	this.hasRobot.setValue(this.model.hasRobot);
	
	this.robotCallUpTime.setValue(this.model.robotCallUpTime);
	this.robotMaxCount.setValue(this.model.robotMaxCount);
	this.robotOpTimeMin.setValue(this.model.robotOpTimeMin);
	this.robotOpTimeMax.setValue(this.model.robotOpTimeMax);

	console.log('<<< NormalRoomModelView.prototype._updateViewImpl');
}

NormalRoomModelView.prototype._checkValidImpl = function() {
	console.log('>>> NormalRoomModelView.prototype._checkValid');
	
	this.buyinChip.checkValid();
	this.minCoin.checkValid();
	this.maxCoin.checkValid();
	this.minCoinQS.checkValid();
	this.maxCoinQS.checkValid();
	this.roomFee.checkValid();
	this.roomMutil.checkValid();
	this.roomLevel.checkValid();
	this.winDesc.checkValid();
	
	this.sendCoupon.checkValid();
	this.showCard.checkValid();
	this.goodCard.checkValid();
	
	this.lucky.checkValid();
	this.canChat.checkValid();
	this.unticheat.checkValid();
	this.gslam.checkValid();
	this.cardNoteChip.checkValid();
	
	this.opTime.checkValid();
	this.robotTimes.checkValid();
	this.passTime.checkValid();
	
	this.rangPaiMultiType.checkValid();
	this.hasRobot.checkValid();
	
	this.robotCallUpTime.checkValid();
	this.robotMaxCount.checkValid();
	this.robotOpTimeMin.checkValid();
	this.robotOpTimeMax.checkValid();
	
	console.log('<<< NormalRoomModelView.prototype._checkValid');
}

NormalRoomModelView.prototype._updateModelImpl = function() {
	console.log('>>> NormalRoomModelView.prototype._updateModelImpl');
	console.log('<<< NormalRoomModelView.prototype._updateModelImpl');
}

function MatchRoomModelView(node, model) {
	RoomModelView.call(this, node, model);
}

inheritPrototype(MatchRoomModelView, RoomModelView);

MatchRoomModelView.prototype._initViewImpl = function() {
	console.log('>>> MatchRoomModelView.prototype._initViewImpl');

	/*
	this.buyinChip = new NumberInputControl(this.getElementByName('buyinChip'), '带入必须是整数');
	this.minCoin = new NumberInputControl(this.getElementByName('minCoin'), '准入必须是整数');
	this.maxCoin = new NumberInputControl(this.getElementByName('maxCoin'), '准入必须是整数');
	this.minCoinQS = new NumberInputControl(this.getElementByName('minCoinQS'), '快开必须是整数');
	this.maxCoinQS = new NumberInputControl(this.getElementByName('maxCoinQS'), '快开必须是整数');
	this.roomFee = new NumberInputControl(this.getElementByName('roomFee'), '服务费必须是整数');
	this.roomMutil = new NumberInputControl(this.getElementByName('roomMutil'), '底注必须是整数');
	*/
	this.roomLevel = new NumberInputControl(this.getElementByName('roomLevel'), '房间级别必须是整数');
	/*
	this.winDesc = new InputControl(this.getElementByName('winDesc'), '');
	this.sendCoupon = new SelectControl(this.getElementByName('sendCoupon'), '请选择是否送券', boolNameValues);
	this.showCard = new SelectControl(this.getElementByName('showCard'), '请选择是否明牌', boolNameValues);
	this.goodCard = new SelectControl(this.getElementByName('goodCard'), '请选择是否有好牌', boolNameValues);
	this.lucky = new LimitNumberInputControl(this.getElementByName('lucky'), '请选择是否送', 0, 100);
	*/
	this.canChat = new SelectControl(this.getElementByName('canChat'), '请选择是否送券', boolNameValues);
	this.unticheat = new SelectControl(this.getElementByName('unticheat'), '请选择是否送券', boolNameValues);
	
	this.gslam = new NumberInputControl(this.getElementByName('gslam'), '大满贯倍数必须是整数');
	this.cardNoteChip = new NumberInputControl(this.getElementByName('cardNoteChip'), '牌局记牌器价格必须是整数');
	
	this.opTime = new NumberInputControl(this.getElementByName('opTime'), '操作超时必须是整数');
	this.robotTimes = new NumberInputControl(this.getElementByName('robotTimes'), '托管超时次数必须是整数');
	this.passTime = new NumberInputControl(this.getElementByName('passTime'), '过牌超时必须是整数');
	
	/*
	this.rangPaiMultiType = new SelectControl(this.getElementByName('rangPaiMultiType'), '请选择二斗让牌倍数类型', rangpaiMutilTypeNameValues);
	*/
	this.hasRobot = new SelectControl(this.getElementByName('hasRobot'), '请选择是否有机器人', boolNameValues);
	
	this.robotCallUpTime = new NumberInputControl(this.getElementByName('robotCallUpTime'), '机器人唤醒时间必须是整数');
	this.robotMaxCount = new NumberInputControl(this.getElementByName('robotMaxCount'), '机器人数量必须是整数');
	this.robotOpTimeMin = new NumberInputControl(this.getElementByName('robotOpTimeMin'), '机器人操作时间必须是整数');
	this.robotOpTimeMax = new NumberInputControl(this.getElementByName('robotOpTimeMax'), '机器人操作时间必须是整数');
	
	console.log('<<< MatchRoomModelView.prototype._initViewImpl');
}

MatchRoomModelView.prototype._updateViewImpl = function() {
	console.log('>>> MatchRoomModelView.prototype._updateViewImpl');
	
	/*
	this.buyinChip.setValue(this.model.buyinChip);
	this.minCoin.setValue(this.model.minCoin);
	this.maxCoin.setValue(this.model.maxCoin);
	this.minCoinQS.setValue(this.model.minCoinQS);
	this.maxCoinQS.setValue(this.model.maxCoinQS);
	this.roomFee.setValue(this.model.roomFee);
	this.roomMutil.setValue(this.model.roomMutil);
	*/
	this.roomLevel.setValue(this.model.roomLevel);
	/*
	this.winDesc.setValue(this.model.winDesc);
	this.sendCoupon.setValue(this.model.sendCoupon);
	this.showCard.setValue(this.model.showCard);
	this.goodCard.setValue(this.model.goodCard);
	this.lucky.setValue(this.model.lucky);
	*/
	this.canChat.setValue(this.model.canChat);
	this.unticheat.setValue(this.model.unticheat);
	this.gslam.setValue(this.model.gslam);
	this.cardNoteChip.setValue(this.model.cardNoteChip);
	
	this.opTime.setValue(this.model.opTime);
	this.robotTimes.setValue(this.model.robotTimes);
	this.passTime.setValue(this.model.passTime);
	
	/*
	this.rangPaiMultiType.setValue(this.model.rangPaiMultiType);
	*/
	this.hasRobot.setValue(this.model.hasRobot);
	
	this.robotCallUpTime.setValue(this.model.robotCallUpTime);
	this.robotMaxCount.setValue(this.model.robotMaxCount);
	this.robotOpTimeMin.setValue(this.model.robotOpTimeMin);
	this.robotOpTimeMax.setValue(this.model.robotOpTimeMax);

	console.log('<<< MatchRoomModelView.prototype._updateViewImpl');
}

MatchRoomModelView.prototype._checkValidImpl = function() {
	console.log('>>> MatchRoomModelView.prototype._checkValid');
	
	/*
	this.buyinChip.checkValid();
	this.minCoin.checkValid();
	this.maxCoin.checkValid();
	this.minCoinQS.checkValid();
	this.maxCoinQS.checkValid();
	this.roomFee.checkValid();
	this.roomMutil.checkValid();
	*/
	this.roomLevel.checkValid();
	/*
	this.winDesc.checkValid();
	this.sendCoupon.checkValid();
	this.showCard.checkValid();
	this.goodCard.checkValid();
	this.lucky.checkValid();
	*/
	
	this.canChat.checkValid();
	this.unticheat.checkValid();
	this.gslam.checkValid();
	this.cardNoteChip.checkValid();
	
	this.opTime.checkValid();
	this.robotTimes.checkValid();
	this.passTime.checkValid();
	/*
	this.rangPaiMultiType.checkValid();
	*/
	this.hasRobot.checkValid();
	
	this.robotCallUpTime.checkValid();
	this.robotMaxCount.checkValid();
	this.robotOpTimeMin.checkValid();
	this.robotOpTimeMax.checkValid();
	
	console.log('<<< MatchRoomModelView.prototype._checkValid');
}

MatchRoomModelView.prototype._updateModelImpl = function() {
	console.log('>>> MatchRoomModelView.prototype._updateModelImpl');
	console.log('<<< MatchRoomModelView.prototype._updateModelImpl');
}

function ArenaMatchRoomModelView(node, model) {
	RoomModelView.call(this, node, model);
}

inheritPrototype(ArenaMatchRoomModelView, MatchRoomModelView);


ArenaMatchRoomModelView.prototype._initViewImpl = function() {
	console.log('>>> ArenaMatchRoomModelView.prototype._initViewImpl');
	MatchRoomModelView.prototype._initViewImpl.apply(this);
	console.log('<<< ArenaMatchRoomModelView.prototype._initViewImpl');
}

ArenaMatchRoomModelView.prototype._updateViewImpl = function() {
	console.log('>>> ArenaMatchRoomModelView.prototype._updateViewImpl');
	MatchRoomModelView.prototype._updateViewImpl.apply(this);
	console.log('<<< ArenaMatchRoomModelView.prototype._updateViewImpl');
}

ArenaMatchRoomModelView.prototype._checkValidImpl = function() {
	console.log('>>> MatchRoomModelView.prototype._checkValid');
	MatchRoomModelView.prototype._checkValidImpl.apply(this);
	console.log('<<< ArenaMatchRoomModelView.prototype._checkValid');
}

ArenaMatchRoomModelView.prototype._updateModelImpl = function() {
	console.log('>>> ArenaMatchRoomModelView.prototype._updateModelImpl');
	MatchRoomModelView.prototype._updateModelImpl.apply(this);
	console.log('<<< ArenaMatchRoomModelView.prototype._updateModelImpl');
}


function GroupMatchRoomModelView(node, model) {
	RoomModelView.call(this, node, model);
}

inheritPrototype(GroupMatchRoomModelView, MatchRoomModelView);


GroupMatchRoomModelView.prototype._initViewImpl = function() {
	console.log('>>> GroupMatchRoomModelView.prototype._initViewImpl');
	MatchRoomModelView.prototype._initViewImpl.apply(this);
	console.log('<<< GroupMatchRoomModelView.prototype._initViewImpl');
}

GroupMatchRoomModelView.prototype._updateViewImpl = function() {
	console.log('>>> GroupMatchRoomModelView.prototype._updateViewImpl');
	MatchRoomModelView.prototype._updateViewImpl.apply(this);
	console.log('<<< GroupMatchRoomModelView.prototype._updateViewImpl');
}

GroupMatchRoomModelView.prototype._checkValidImpl = function() {
	console.log('>>> MatchRoomModelView.prototype._checkValid');
	MatchRoomModelView.prototype._checkValidImpl.apply(this);
	console.log('<<< GroupMatchRoomModelView.prototype._checkValid');
}

GroupMatchRoomModelView.prototype._updateModelImpl = function() {
	console.log('>>> GroupMatchRoomModelView.prototype._updateModelImpl');
	MatchRoomModelView.prototype._updateModelImpl.apply(this);
	console.log('<<< GroupMatchRoomModelView.prototype._updateModelImpl');
}

