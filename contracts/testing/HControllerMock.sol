// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;


interface OffchainBorrowingGauge {
    function user_checkpoint(address borrower) external;
}


/**
 * @title Hundred's Controller Contract Mock
 * @author Hundred Finance
 */
contract HControllerMock {
    struct OutboundBorrow {
        uint chainId;
        address cToken;
        uint borrowBalance;
    }

    mapping(address => OutboundBorrow[]) public accountOutboundBorrows;
    mapping(uint => mapping(address => uint256)) public totalOutboundBorrows;
    mapping(address => uint) public totalOutboundBorrowsPerGauge;
    mapping(uint => mapping(address => address)) public borrowGauges;

    function registerBorrowGauge(uint borrowChainId, address cToken, address gauge) public {
        require(totalOutboundBorrows[borrowChainId][cToken] == 0);
        require(borrowGauges[borrowChainId][cToken] == address(0));

        borrowGauges[borrowChainId][cToken] = gauge;
    }

    function increaseBorrowPosition(
        uint borrowChainId,
        address borrower,
        address cToken,
        uint borrowAmount
    ) public {
        OutboundBorrow[] memory borrowPositions = accountOutboundBorrows[borrower];

        uint len = borrowPositions.length;
        uint positionIndex = len;
        for (uint i = 0; i < len; i++) {
            if (borrowPositions[i].cToken == cToken && borrowPositions[i].chainId == borrowChainId) {
                positionIndex = i;
                break;
            }
        }

        if (positionIndex < len) {
            accountOutboundBorrows[borrower][positionIndex].borrowBalance += borrowAmount;
        } else {
            OutboundBorrow memory borrowPosition;

            borrowPosition.chainId = borrowChainId;
            borrowPosition.cToken = cToken;
            borrowPosition.borrowBalance = borrowAmount;

            accountOutboundBorrows[borrower].push(borrowPosition);
        }

        totalOutboundBorrows[borrowChainId][cToken] += borrowAmount;

        address borrowGaugeForToken = borrowGauges[borrowChainId][cToken];
        if (borrowGaugeForToken != address(0)) {
            totalOutboundBorrowsPerGauge[borrowGaugeForToken] += borrowAmount;
            OffchainBorrowingGauge(borrowGaugeForToken).user_checkpoint(borrower);
        }
    }

    function reduceBorrowPosition(
        uint borrowChainId,
        address borrower,
        address cToken,
        uint repayAmount
    ) public {
        OutboundBorrow[] memory borrowPositions = accountOutboundBorrows[borrower];

        uint len = borrowPositions.length;
        uint positionIndex = len;
        for (uint i = 0; i < len; i++) {
            if (borrowPositions[i].cToken == cToken && borrowPositions[i].chainId == borrowChainId) {
                positionIndex = i;
                break;
            }
        }

        if (positionIndex < len) {
            accountOutboundBorrows[borrower][positionIndex].borrowBalance -= repayAmount;
        }

        totalOutboundBorrows[borrowChainId][cToken] -= repayAmount;

        address borrowGaugeForToken = borrowGauges[borrowChainId][cToken];
        if (borrowGaugeForToken != address(0)) {
            totalOutboundBorrowsPerGauge[borrowGaugeForToken] -= repayAmount;
            OffchainBorrowingGauge(borrowGaugeForToken).user_checkpoint(borrower);
        }
    }

    function resetBorrowPosition(
        uint borrowChainId,
        address borrower,
        address cToken,
        uint borrowBalance
    ) internal {
        OutboundBorrow[] memory borrowPositions = accountOutboundBorrows[borrower];

        uint len = borrowPositions.length;
        uint positionIndex = len;
        for (uint i = 0; i < len; i++) {
            if (borrowPositions[i].cToken == cToken && borrowPositions[i].chainId == borrowChainId) {
                positionIndex = i;
                break;
            }
        }

        if (positionIndex < len) {
            accountOutboundBorrows[borrower][positionIndex].borrowBalance = borrowBalance;
        }
    }

    function accountOffchainBorrowsForGauge(address borrower) public view returns (uint256 total) {
        OutboundBorrow[] memory borrowPositions = accountOutboundBorrows[borrower];
        for (uint i = 0; i < borrowPositions.length; i++) {
            address borrowGaugeForToken = borrowGauges[borrowPositions[i].chainId][borrowPositions[i].cToken];
            if (borrowGaugeForToken == msg.sender) {
                total += borrowPositions[i].borrowBalance;
            }
        }
    }

    function totalOffchainBorrowsForGauge() public view returns (uint256) {
        return totalOutboundBorrowsPerGauge[msg.sender];
    }
}
