function object(o) {
    function F() {
    }
    F.prototype = o;
    return new F();
}

function inheritPrototype(subType, superType) {
    var prototype = object(superType.prototype);
    prototype.constructor = subType;
    subType.prototype = prototype;
}

function trim(str) {
	return str.replace(/(^\s*)|(\s*$)/g, '');
}

function ltrim(str){
	return str.replace(/(^\s*)/g, '');
}

function rtrim(str){
	return str.replace(/(\s*$)/g, '');
}

function isInt(value) {
	return (typeof(value) === 'number') && (parseInt(value, 10) === value);
}

function isBoolInt(value) {
	return isInt(value) && (value === 0 || value === 1); 
}

function isString(value) {
	return typeof(value) === 'string';
}

function isArray(value) {
	return value instanceof Array;
}

function checkString(obj, field) {
	var value = obj[field];
	if (!isString(value)) {
		throw new Error('Field ' + field + ' must be string: ' + value);
	}
	return value;
}

function checkInt(obj, field) {
	var value = obj[field];
	if (!isInt(value)) {
		throw new Error('Field ' + field + ' must be int: ' + value);
	}
	return value;
}

function checkIntDefault(obj, field, defVal) {
	var value = obj[field];
	if (value == undefined) {
		return defVal;
	}
	if (!isInt(value)) {
		throw new Error('Field ' + field + ' must be int: ' + value);
	}
	return value;
}

function checkBoolInt(obj, field) {
	var value = obj[field];
	if (!isBoolInt(value)) {
		throw new Error('Field ' + field + ' must be int in (0, 1): ' + value);
	}
	return value;
}

function checkIntArray(obj, field) {
	var value = obj[field];
	if (!isArray(value)) {
		throw new Error('Field ' + field + ' must be list: ' + value);
	}
	for (var i = 0; i < value.length; i++) {
		if (!isInt(value[i])) {
			throw new Error('Field ' + field + ' must be int list: ' + value);
		}
	}
	return value;
}

function removeAllChild(elt) {
    while(elt.hasChildNodes()) {
        elt.removeChild(elt.firstChild);
    }
}

function InvalidateDataException(control, message) {
	Error.call(this);
	this.name = 'InvalidateDataException';
	this.message = message;
	this.control = control;
}

function Control(element, invalidTips) {
	this.element = element;
	this.invalidTips = invalidTips;
}

Control.prototype.getValue = function() {
	throw new Error('Not implement');
}

Control.prototype.setValue = function(value) {
	if (!this.isValidValue(value)) {
		throw new Error('Set bad value: ' + value + ':' + typeof(value));
	}
	this._setValueImpl(value);
}

Control.prototype.isValidValue = function(value) {
	return true;
}

Control.prototype.isValidForView = function() {
	return true;
}

Control.prototype.isValid = function() {
	return true;
}

Control.prototype.checkValid = function() {
	if (!this.isValid()) {
		throw new InvalidateDataException(this, this.invalidTips);
	}
}

Control.prototype._setValueImpl = function(value) {
	throw new Error('Not implement');
}

function InputControl(element, invalidTips) {
	Control.call(this, element, invalidTips);
	this._value = element.value || '';
	var self = this;
	this.element.onchange = function() {
		self.onChanged();
	};
	this.element.onkeyup = function() {
		self.onChanged();
	};
	this.element.onblur = function() {
		console.log('InputControl.onblur value=', self.element.value, '_value=', self._value);
		if (!self.isValid()) {
			self.element.value = self._value;
		}
	}
}

inheritPrototype(InputControl, Control);

InputControl.prototype.getValue = function() {
	return this.element.value;
}

InputControl.prototype._setValueImpl = function(value) {
	this.element.value = value;
	this._value = value;
}

InputControl.prototype.isValid = function() {
	return true;
}

InputControl.prototype.onChanged = function() {
	if (!this.isValidForView()) {
		this.element.value = this._value;
	} else if (this.isValid()) {
		this._value = this.element.value;
	}
}

function NotEmptyInputControl(element, invalidTips) {
	InputControl.call(this, element, invalidTips);
}

inheritPrototype(NotEmptyInputControl, InputControl);

NotEmptyInputControl.prototype.checkValid = function() {
	if (trim(this.element.value) === '') {
		throw new InvalidateDataException(this, this.invalidTips);
	}
}

function NumberInputControl(element, invalidTips) {
	InputControl.call(this, element, invalidTips);
}

inheritPrototype(NumberInputControl, InputControl);

NumberInputControl.prototype.isValidForView = function() {
	// 输入阶段可以是空串
	if (this.element.value === '') {
		return true;
	}
	return this.isValid();
}

NumberInputControl.prototype.isValid = function() {
	return !isNaN(this.element.value) && !isNaN(parseInt(this.element.value));
}

NumberInputControl.prototype.isValidValue = function(value) {
	console.log('NumberInputControl.prototype.isValidValue value=', value, typeof(value));
	return typeof(value) === 'number';
}

function LimitNumberInputControl(element, invalidTips, minValue, maxValue) {
	InputControl.call(this, element, invalidTips);
	this._minValue = minValue;
	this._maxValue = maxValue;
}

inheritPrototype(LimitNumberInputControl, InputControl);

LimitNumberInputControl.prototype.isValidForView = function() {
	// 输入阶段可以是空串
	if (this.element.value === '') {
		return true;
	}
	return this.isValid();
}

LimitNumberInputControl.prototype.isValidValue = function(value) {
	return (typeof(value) === 'number'
			&& (this._minValue === null || value >= this._minValue)
			&& (this._maxValue === null || value <= this._maxValue));
}

LimitNumberInputControl.prototype.isValid = function() {
	value = parseInt(this.element.value);
	return (!isNaN(value)
			&& !isNaN(this.element.value)
			&& (this._minValue === null || value >= this._minValue)
			&& (this._maxValue === null || value <= this._maxValue));
}

function SelectControl(element, invalidTips, nameValues) {
	Control.call(this, element, invalidTips);
	this._nameValues = nameValues;
	this.element.options.length = 0;
	console.log('SelectControl nameValues=', nameValues);
	for (var i = 0; i < this._nameValues.length; i++) {
		nameValue = this._nameValues[i];
		var item = new Option(nameValue['name'], nameValue['value']);
		this.element.options.add(item);
	}
}

inheritPrototype(SelectControl, Control);

SelectControl.prototype.isValid = function() {
	return this.element.options.selectedIndex >= 0;
}

SelectControl.prototype.getValue = function() {
	return this._nameValues[this.element.options.selectIndex]['value'];
}

SelectControl.prototype.isValidValue = function(value) {
	for (var i = 0; i < this._nameValues.length; i++) {
		if (this._nameValues[i].value === value) {
			return true;
		}
	}
	return false;
}

SelectControl.prototype._setValueImpl = function(value) {
	for (var i = 0; i < this._nameValues.length; i++) {
		if (this._nameValues[i].value === value) {
			this.element.options[i].selected = true;
			return
		}
	}
	throw new Error('Set bad value: ' + value + ':' + typeof(value));
}


